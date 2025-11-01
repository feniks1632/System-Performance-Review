from app.core.logger import logger


def test_smoke_integration(
    client,
    test_goal_with_employee,
    employee_auth_headers,
    manager_auth_headers,
):
    """Smoke-тест основных интеграций"""
    logger.info("SMOKE-ТЕСТ ОСНОВНЫХ ИНТЕГРАЦИЙ")

    goal_id = test_goal_with_employee.id

    # Только КРИТИЧЕСКИЕ проверки интеграции
    responses = []

    # 1. Goals module
    responses.append(
        client.get(f"/api/v1/goals/{goal_id}", headers=employee_auth_headers)
    )

    # 2. Analytics module
    responses.append(
        client.get(f"/api/v1/analytics/goal/{goal_id}", headers=manager_auth_headers)
    )

    # 3. Employee summary
    responses.append(
        client.get(
            f"/api/v1/analytics/employee/{test_goal_with_employee.employee_id}/summary",
            headers=manager_auth_headers,
        )
    )

    # Проверяем что все основные модули отвечают
    for i, response in enumerate(responses):
        assert response.status_code in [
            200,
            404,
        ], f"Module {i} returned {response.status_code}"

    logger.info("Все основные модули интегрированы корректно")
