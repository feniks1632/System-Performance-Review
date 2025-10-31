from datetime import datetime, timedelta
from unittest.mock import patch

from app.models.database import Goal, User


class TestEmailService:

    def test_notify_manager_about_pending_review_success(
        self, email_service, db_session
    ):
        """Тест уведомления менеджера о готовности ревью"""
        # Создаем тестовую цель
        user = User(
            email="employee@test.com",
            full_name="Test Employee",
            hashed_password="hashed",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        goal = Goal(
            title="Test Goal",
            description="Test Description",
            expected_result="Test Result",
            deadline=datetime.now() + timedelta(days=30),
            employee_id=user.id,
        )
        db_session.add(goal)
        db_session.commit()

        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = True

            result = email_service.notify_manager_about_pending_review(
                goal_id=goal.id,
                employee_name="Test Employee",
                manager_email="manager@test.com",
            )

            assert result is True
            mock_send.assert_called_once()

            call_args = mock_send.call_args
            print(f"DEBUG call_args type: {type(call_args)}")
            print(f"DEBUG call_args: {call_args}")

            # Универсальный способ извлечения аргументов
            call_kwargs = call_args[1] if call_args and call_args[1] else {}
            call_args_list = call_args[0] if call_args and call_args[0] else []

            # Пробуем разные способы извлечения to_email
            to_email = None
            if "to_email" in call_kwargs:
                to_email = call_kwargs["to_email"]
            elif len(call_args_list) > 0:
                to_email = call_args_list[0]  # первый позиционный аргумент

            print(f"DEBUG extracted to_email: {to_email}")

            assert to_email == "manager@test.com"

    def test_notify_respondents_about_review_request_success(
        self, email_service, db_session
    ):
        """Тест уведомления респондентов"""
        # Создаем тестовую цель
        user = User(
            email="employee@test.com",
            full_name="Test Employee",
            hashed_password="hashed",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        goal = Goal(
            title="Test Goal",
            description="Test Description",
            expected_result="Test Result",
            deadline=datetime.now() + timedelta(days=30),
            employee_id=user.id,
        )
        db_session.add(goal)
        db_session.commit()

        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = True

            respondent_emails = ["resp1@test.com", "resp2@test.com"]

            result = email_service.notify_respondents_about_review_request(
                goal_id=goal.id,
                employee_name="Test Employee",
                respondent_emails=respondent_emails,
            )

            assert result is True
            assert mock_send.call_count == 2

            # Собираем все email адреса из вызовов
            sent_emails = []
            for call in mock_send.call_args_list:
                kwargs = call[1] if call[1] else {}
                args = call[0] if call[0] else []

                if "to_email" in kwargs:
                    sent_emails.append(kwargs["to_email"])
                elif len(args) > 0:
                    sent_emails.append(args[0])

            print(f"DEBUG sent_emails: {sent_emails}")
            assert set(sent_emails) == set(respondent_emails)

    def test_notify_employee_about_final_review_success(
        self, email_service, db_session
    ):
        """Тест уведомления сотрудника о завершении ревью"""
        # Создаем тестовую цель
        user = User(
            email="employee@test.com",
            full_name="Test Employee",
            hashed_password="hashed",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        goal = Goal(
            title="Test Goal",
            description="Test Description",
            expected_result="Test Result",
            deadline=datetime.now() + timedelta(days=30),
            employee_id=user.id,
        )
        db_session.add(goal)
        db_session.commit()

        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = True

            result = email_service.notify_employee_about_final_review(
                goal_id=goal.id,
                employee_email="employee@test.com",
                manager_name="Test Manager",
                final_rating="A",
            )

            assert result is True
            mock_send.assert_called_once()

            call_args = mock_send.call_args
            kwargs = call_args[1] if call_args and call_args[1] else {}
            args = call_args[0] if call_args and call_args[0] else []

            to_email = None
            if "to_email" in kwargs:
                to_email = kwargs["to_email"]
            elif len(args) > 0:
                to_email = args[0]

            assert to_email == "employee@test.com"
