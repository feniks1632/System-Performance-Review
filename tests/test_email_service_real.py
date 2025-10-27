# tests/test_email_real.py
import pytest
from app.services.email_service import EmailService


def test_email_service_real_methods(email_service):
    """Тест реальных методов EmailService (без mock)"""
    # Просто проверяем что методы существуют и вызываются
    try:
        # notify_manager_about_pending_review
        result1 = email_service.notify_manager_about_pending_review(
            goal_id="test-goal-id",
            employee_name="Test Employee",
            manager_email="manager@test.com",
        )
        print(f"notify_manager result: {result1}")

        # notify_respondents_about_review_request
        result2 = email_service.notify_respondents_about_review_request(
            goal_id="test-goal-id",
            employee_name="Test Employee",
            respondent_emails=["test1@test.com", "test2@test.com"],
        )
        print(f"notify_respondents result: {result2}")

        # notify_employee_about_final_review
        result3 = email_service.notify_employee_about_final_review(
            goal_id="test-goal-id",
            employee_email="employee@test.com",
            manager_name="Test Manager",
            final_rating="A",
        )
        print(f"notify_employee result: {result3}")

    except Exception as e:
        print(f"Error in email service methods: {e}")
        pytest.fail(f"Email service methods should not raise exceptions: {e}")
