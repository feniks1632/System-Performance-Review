from app.core.logger import logger


def test_error_handling_integration(
    client,
    employee_auth_headers,
    manager_auth_headers,
):
    """Тест интеграции обработки ошибок между модулями"""
    logger.info("ТЕСТ ИНТЕГРАЦИИ ОБРАБОТКИ ОШИБОК")

    # 1. Попытка доступа к несуществующей цели
    response = client.get(
        "/api/v1/analytics/goal/non-existent-goal-id", headers=manager_auth_headers
    )
    assert response.status_code == 404

    # 2. Попытка создать ревью для несуществующей цели
    invalid_review_data = {
        "goal_id": "non-existent-goal-id",
        "review_type": "self",
        "answers": [],
    }

    response = client.post(
        "/api/v1/reviews/", json=invalid_review_data, headers=employee_auth_headers
    )
    assert response.status_code in [400, 404, 422]

    # 3. Попытка получить аналитику по сотруднику без целей
    # (если такой сценарий возможен в вашей системе)

    response = client.get(
        "/api/v1/analytics/goal/{goal_id}", headers=employee_auth_headers
    )
    assert response.status_code in [400, 404, 422]

    logger.info("Интеграция обработки ошибок работает")
