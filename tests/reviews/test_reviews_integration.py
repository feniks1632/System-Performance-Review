from app.models.schemas import ReviewType
from app.core.logger import logger


class TestReviewsIntegration:
    def test_create_self_review(self, client, auth_headers, test_goal_data):
        """Тест создания самооценки"""
        # Создаем цель
        goal_response = client.post(
            "/api/v1/goals/", json=test_goal_data, headers=auth_headers
        )
        assert goal_response.status_code == 200
        goal_id = goal_response.json()["id"]

        # Создаем самооценку
        review_data = {
            "goal_id": goal_id,
            "review_type": ReviewType.SELF,
            "answers": [
                {"question_id": "q1", "answer": "Хорошо выполнил", "score": 4.5}
            ],
        }

        response = client.post(
            "/api/v1/reviews/", json=review_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["review_type"] == ReviewType.SELF
        assert data["goal_id"] == goal_id

    def test_manager_review_flow(self, client, db_session):
        """Тест оценки руководителя"""
        from app.core.security import get_password_hash
        from app.models.database import User, Goal

        # Создаем сотрудника
        employee = User(
            email="employee_manager_test@test.com",
            full_name="Manager Test Employee",
            hashed_password=get_password_hash("password123"),
            is_manager=False,
        )
        db_session.add(employee)

        # Создаем менеджера
        manager = User(
            email="manager_test@test.com",
            full_name="Manager Test Manager",
            hashed_password=get_password_hash("password123"),
            is_manager=True,
        )
        db_session.add(manager)

        db_session.commit()
        db_session.refresh(employee)

        # Создаем цель
        goal = Goal(
            title="Manager Review Goal",
            description="Goal for manager review",
            expected_result="Expected result",
            deadline="2024-12-31T23:59:59",
            employee_id=employee.id,
        )
        db_session.add(goal)
        db_session.commit()

        # Логинимся менеджером
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "manager_test@test.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        manager_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Создаем оценку руководителя
        review_data = {
            "goal_id": goal.id,
            "review_type": ReviewType.MANAGER,
            "answers": [
                {"question_id": "q1", "answer": "Хорошая работа", "score": 4.0}
            ],
        }

        review_response = client.post(
            "/api/v1/reviews/", json=review_data, headers=manager_headers
        )
        assert review_response.status_code == 200

        data = review_response.json()
        assert data["review_type"] == ReviewType.MANAGER
        assert data["goal_id"] == goal.id

    def test_unauthorized_respondent_review(self, client, auth_headers, test_goal_data):
        """Тест что не-респондент не может оценивать цель"""
        # Создаем цель (без респондентов)
        goal_response = client.post(
            "/api/v1/goals/", json=test_goal_data, headers=auth_headers
        )
        assert goal_response.status_code == 200
        goal_id = goal_response.json()["id"]

        # Пытаемся создать оценку респондента (но мы не респондент этой цели)
        review_data = {
            "goal_id": goal_id,
            "answers": [
                {
                    "question_id": "q1",
                    "answer": "Попытка несанкционированной оценки",
                    "score": 3.0,
                }
            ],
        }

        response = client.post(
            "/api/v1/reviews/respondent", json=review_data, headers=auth_headers
        )
        assert response.status_code == 403
        assert "Not authorized as respondent" in response.json()["detail"]


def test_review_process_integration(
    client,
    test_goal_with_employee,
    test_question_templates,
    employee_auth_headers,
    manager_auth_headers,
):
    """Тест интеграции: цель → вопросы → ревью → аналитика"""
    logger.info("ТЕСТ ИНТЕГРАЦИИ ПРОЦЕССА РЕВЬЮ")

    goal_id = test_goal_with_employee.id

    # 1. Интеграция: вопросы + создание ревью
    questions_response = client.get(
        "/api/v1/question-templates/?question_type=self", headers=employee_auth_headers
    )
    questions = questions_response.json()

    # Создаем ревью используя полученные вопросы
    review_data = {
        "goal_id": goal_id,
        "review_type": "self",
        "answers": [
            {
                "question_id": questions[0]["id"],
                "answer": "Интеграционный тест: работаю над улучшением навыков",
                "score": 4.0,
            }
        ],
    }

    review_response = client.post(
        "/api/v1/reviews/", json=review_data, headers=employee_auth_headers
    )
    assert review_response.status_code == 200

    # 2. Интеграция: ревью → аналитика
    analytics_response = client.get(
        f"/api/v1/analytics/goal/{goal_id}", headers=manager_auth_headers
    )
    assert analytics_response.status_code == 200

    analytics = analytics_response.json()

    # Проверяем что аналитика учитывает созданное ревью
    assert analytics["goal_id"] == goal_id
    assert "scores" in analytics
    assert "recommendations" in analytics

    logger.info("Интеграция цель→вопросы→ревью→аналитика работает")
