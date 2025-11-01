from app.core.logger import logger


def test_get_current_user(client, test_user_data):
    """Тест получения информации о текущем пользователе"""
    # Регистрируем и логинимся
    client.post("/api/v1/auth/register", json=test_user_data)

    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Получаем информацию о пользователе
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]


def test_protected_endpoint_without_token(client):
    """Тест защищенного endpoint без токена"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_protected_endpoint_invalid_token(client):
    """Тест защищенного endpoint с неверным токеном"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_cross_role_access_integration(
    client,
    test_goal_with_employee,
    employee_auth_headers,
    manager_auth_headers,
):
    """Тест интеграции прав доступа между сотрудником и руководителем"""
    logger.info("🚀 ТЕСТ ИНТЕГРАЦИИ ПРАВ ДОСТУПА")

    goal_id = test_goal_with_employee.id

    # 1. Сотрудник может получить СВОИ цели
    employee_goals_response = client.get(
        f"/api/v1/goals/employee/{test_goal_with_employee.employee_id}",
        headers=employee_auth_headers,
    )
    assert employee_goals_response.status_code == 200

    # 2. Руководитель может получить цели ПОДЧИНЕННОГО
    manager_summary_response = client.get(
        f"/api/v1/analytics/employee/{test_goal_with_employee.employee_id}/summary",
        headers=manager_auth_headers,
    )
    assert manager_summary_response.status_code == 200

    # 3. Проверяем что данные консистентны
    employee_goals = employee_goals_response.json()
    manager_summary = manager_summary_response.json()

    assert len(employee_goals) == manager_summary["total_goals"]

    logger.info("Интеграция прав доступа между ролями работает")


def test_data_consistency_integration(
    client,
    test_goal_with_employee,
    employee_auth_headers,
    manager_auth_headers,
):
    """Тест интеграции консистентности данных между модулями"""
    logger.info("ТЕСТ ИНТЕГРАЦИИ КОНСИСТЕНТНОСТИ ДАННЫХ")

    goal_id = test_goal_with_employee.id

    # 1. Получаем цель из goals модуля
    goal_response = client.get(
        f"/api/v1/goals/{goal_id}", headers=employee_auth_headers
    )
    goal_data = goal_response.json()

    # 2. Получаем аналитику по этой же цели из analytics модуля
    analytics_response = client.get(
        f"/api/v1/analytics/goal/{goal_id}", headers=manager_auth_headers
    )
    analytics_data = analytics_response.json()

    # 3. Проверяем консистентность данных между модулями
    assert goal_data["id"] == analytics_data["goal_id"]
    assert goal_data["title"] == test_goal_with_employee.title

    # 4. Проверяем сводную аналитику
    summary_response = client.get(
        f"/api/v1/analytics/employee/{test_goal_with_employee.employee_id}/summary",
        headers=manager_auth_headers,
    )
    summary_data = summary_response.json()

    assert summary_data["employee_id"] == test_goal_with_employee.employee_id
    assert summary_data["total_goals"] >= 1  # Должна быть наша тестовая цель

    logger.info("Интеграция консистентности данных работает")
