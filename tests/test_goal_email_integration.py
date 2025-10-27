# tests/test_goal_email_integration.py
import pytest
from unittest.mock import patch
from app.core.security import get_password_hash
from app.models.database import User


class TestGoalEmailIntegration:

    def test_create_goal_with_respondents_sends_emails(
        self, client, auth_headers, db_session
    ):  # используем db_session
        """Тест, что при создании цели с респондентами отправляются письма"""
        # Создаем тестовых респондентов
        respondent1 = User(
            email="respondent1@test.com",
            full_name="Respondent One",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
        )

        respondent2 = User(
            email="respondent2@test.com",
            full_name="Respondent Two",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
        )

        db_session.add_all([respondent1, respondent2])
        db_session.commit()

        goal_data = {
            "title": "Test Goal",
            "description": "Test Description",
            "expected_result": "Test Result",
            "deadline": "2024-12-31T00:00:00",
            "task_link": "https://example.com/task/1",
            "respondent_ids": [respondent1.id, respondent2.id],
        }

        with patch("app.api.endpoints.goals.EmailService") as MockEmailService:
            mock_email_service = MockEmailService.return_value
            mock_email_service.notify_respondents_about_review_request.return_value = (
                True
            )

            # Создаем цель
            response = client.post(
                "/api/v1/goals/", json=goal_data, headers=auth_headers
            )

            assert response.status_code == 200

            # Проверяем, что email сервис был вызван
            mock_email_service.notify_respondents_about_review_request.assert_called_once()

    def test_create_goal_without_respondents_no_emails(self, client, auth_headers):
        """Тест, что при создании цели без респондентов письма не отправляются"""
        goal_data = {
            "title": "Test Goal",
            "description": "Test Description",
            "expected_result": "Test Result",
            "deadline": "2024-12-31T00:00:00",
            "task_link": "https://example.com/task/1",
            "respondent_ids": [],
        }

        with patch("app.api.endpoints.goals.EmailService") as MockEmailService:
            mock_email_service = MockEmailService.return_value

            response = client.post(
                "/api/v1/goals/", json=goal_data, headers=auth_headers
            )

            assert response.status_code == 200
            # Проверяем, что email сервис НЕ был вызван
            mock_email_service.notify_respondents_about_review_request.assert_not_called()

    def test_create_goal_email_service_error_does_not_break_flow(
        self, client, auth_headers, db_session
    ):  # Используем db_session
        """Тест, что ошибка email сервиса не ломает создание цели"""
        # Создаем тестового респондента
        respondent = User(
            email="respondent@test.com",
            full_name="Test Respondent",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
        )
        db_session.add(respondent)
        db_session.commit()

        goal_data = {
            "title": "Test Goal",
            "description": "Test Description",
            "expected_result": "Test Result",
            "deadline": "2024-12-31T00:00:00",
            "task_link": "https://example.com/task/1",
            "respondent_ids": [respondent.id],
        }

        with patch("app.api.endpoints.goals.EmailService") as MockEmailService:
            mock_email_service = MockEmailService.return_value
            mock_email_service.notify_respondents_about_review_request.return_value = (
                False
            )

            # Создаем цель - должна создаться даже при ошибке email
            response = client.post(
                "/api/v1/goals/", json=goal_data, headers=auth_headers
            )

            assert response.status_code == 200
            assert "id" in response.json()
            # Email сервис все равно должен быть вызван
            mock_email_service.notify_respondents_about_review_request.assert_called_once()
