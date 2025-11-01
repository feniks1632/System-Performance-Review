from unittest.mock import patch

from app.core.logger import logger


def test_notification_workflow_integration(
    client,
    test_goal_with_employee,
    test_question_templates,
    employee_auth_headers,
    manager_auth_headers,
    mock_smtp,  # Используем mock чтобы не дублировать тесты email
):
    """Тест интеграции: создание ревью → уведомления"""
    logger.info("ТЕСТ ИНТЕГРАЦИИ WORKFLOW УВЕДОМЛЕНИЙ")

    goal_id = test_goal_with_employee.id

    # Создаем ревью (должно trigger-нуть уведомления)
    questions_response = client.get(
        "/api/v1/question-templates/?question_type=manager",
        headers=manager_auth_headers,
    )
    questions = questions_response.json()

    review_data = {
        "goal_id": goal_id,
        "review_type": "manager",
        "answers": [
            {
                "question_id": questions[0]["id"],
                "answer": "Интеграционный тест уведомлений",
                "score": 8.5,
            }
        ],
    }

    with patch(
        "app.services.email_service.EmailService.notify_employee_about_final_review"
    ) as mock_notify:
        mock_notify.return_value = True

        review_response = client.post(
            "/api/v1/reviews/", json=review_data, headers=manager_auth_headers
        )
        assert review_response.status_code == 200

        # Проверяем что система ПЫТАЛАСЬ отправить уведомление
        # (конкретную логику отправки тестируем в test_email_service.py)
        mock_notify.assert_called_once()

    logger.info("Интеграция workflow уведомлений работает")
