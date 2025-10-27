# tests/test_email_content.py
import pytest
import base64
from unittest.mock import patch
from datetime import datetime, timedelta
from app.models.database import User, Goal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEmailContent:

    def test_email_content_contains_company_info(self, email_service, mock_smtp):
        """Тест, что письма содержат информацию о компании"""
        mock_smtp, mock_instance = mock_smtp

        email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        # Получаем отправленное сообщение
        sent_message = mock_instance.send_message.call_args[0][0]

        # Получаем тело письма (может быть base64 encoded)
        email_payload = sent_message.get_payload()[0]
        email_body = email_payload.get_payload()

        # Декодируем base64 если нужно
        try:
            # Пробуем декодировать base64
            decoded_body = base64.b64decode(email_body).decode("utf-8")
            email_body = decoded_body
        except:
            # Если не base64, оставляем как есть
            pass

        # Проверяем содержимое (на русском языке)
        assert "Your Company Name" in email_body
        assert "автоматическое сообщение" in email_body.lower()  # Ищем русский текст

    def test_manager_notification_content(self, email_service, db_session):
        """Тест контента письма для менеджера"""
        # Создаем тестовую цель
        user = User(
            email="employee@test.com",
            full_name="Иван Иванов",
            hashed_password="hashed",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        goal = Goal(
            title="Разработка нового функционала",
            description="Разработать новый модуль системы",
            expected_result="Модуль в продакшене",
            deadline=datetime.now() + timedelta(days=30),
            employee_id=user.id,
        )
        db_session.add(goal)
        db_session.commit()

        with patch.object(email_service, "send_email") as mock_send:
            # Настраиваем mock чтобы он возвращал True при вызове
            mock_send.return_value = True

            result = email_service.notify_manager_about_pending_review(
                goal_id=goal.id,
                employee_name="Иван Иванов",
                manager_email="manager@test.com",
            )

            # Проверяем что метод был вызван
            assert mock_send.called

            # Получаем аргументы вызова
            call_args = mock_send.call_args

            # Извлекаем html_content из аргументов
            html_content = ""
            if call_args:
                # Пробуем получить из именованных аргументов
                if call_args[1]:
                    html_content = call_args[1].get("html_content", "")
                # Или из позиционных аргументов
                elif call_args[0] and len(call_args[0]) >= 3:
                    html_content = call_args[0][2]  # третий позиционный аргумент

            logger.info(f"DEBUG: HTML Content length: {len(html_content)}")
            if html_content:
                logger.info(f"DEBUG: First 500 chars: {html_content[:500]}")

            # Проверяем ключевые элементы контента
            assert "Иван Иванов" in html_content
            assert "Разработка нового функционала" in html_content
            assert "ожидает вашего ревью" in html_content.lower()
