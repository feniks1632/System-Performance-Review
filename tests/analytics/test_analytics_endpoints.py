from datetime import datetime, timedelta

from app.models.database import Goal, User


def test_get_goal_analytics_success(
    client, auth_headers, db_session
):  # используем db_session вместо get_db
    """Тест успешного получения аналитики по цели"""
    # Создаем тестовую цель
    user = db_session.query(User).filter(User.email == "test@example.com").first()

    goal = Goal(
        title="Test Goal",
        description="Test Description",
        expected_result="Test Result",
        deadline=datetime.now() + timedelta(days=30),
        employee_id=user.id,
    )
    db_session.add(goal)
    db_session.commit()

    response = client.get(f"/api/v1/analytics/goal/{goal.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == goal.id
    assert "scores" in data
    assert "recommendations" in data


def test_get_goal_analytics_not_found(client, auth_headers):
    """Тест получения аналитики по несуществующей цели"""
    response = client.get(
        "/api/v1/analytics/goal/non-existent-id", headers=auth_headers
    )

    assert response.status_code == 404
    assert "Goal not found" in response.json()["detail"]


def test_get_employee_summary(
    client, auth_headers, db_session
):  # используем db_session
    """Тест получения сводной аналитики по сотруднику"""
    user = db_session.query(User).filter(User.email == "test@example.com").first()

    response = client.get(
        f"/api/v1/analytics/employee/{user.id}/summary", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == user.id
    assert "total_goals" in data
    assert "average_score" in data
