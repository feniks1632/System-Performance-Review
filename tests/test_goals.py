import pytest
from datetime import datetime, timedelta


def test_create_goal(client, test_user_data):
    """Тест создания цели с аутентификацией"""
    # Сначала регистрируем пользователя
    reg_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_data = reg_response.json()

    # Логинимся чтобы получить токен
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Создаем цель с токеном
    goal_data = {
        "title": "Разработать новую фичу",
        "description": "Разработать и протестировать новую функциональность",
        "expected_result": "Фича готова к продакшену",
        "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "task_link": "https://tasktracker.com/123",
        "respondent_ids": [],
    }

    response = client.post("/api/v1/goals/", json=goal_data, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["title"] == goal_data["title"]
    assert data["employee_id"] == user_data["id"]
    assert data["status"] == "active"


def test_get_employee_goals(client, test_user_data):
    """Тест получения целей сотрудника с аутентификацией"""
    # Регистрируем и логинимся
    reg_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_data = reg_response.json()
    user_id = user_data["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Создаем цель
    goal_data = {
        "title": "Тестовая цель",
        "description": "Описание",
        "expected_result": "Результат",
        "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "respondent_ids": [],
    }

    create_response = client.post("/api/v1/goals/", json=goal_data, headers=headers)
    assert create_response.status_code == 200

    # Получаем цели сотрудника
    response = client.get(f"/api/v1/goals/employee/{user_id}", headers=headers)
    assert response.status_code == 200
    goals = response.json()
    assert len(goals) == 1
    assert goals[0]["title"] == goal_data["title"]
