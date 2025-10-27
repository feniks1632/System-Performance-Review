# tests/test_reviews.py
import pytest
from app.core.security import get_password_hash
from app.models.database import User, Goal, Review
from datetime import datetime, timedelta


def test_create_self_review(client, auth_headers, db_session):  # используем db_session
    """Тест создания самооценки"""
    # Создаем тестовую цель
    user = db_session.query(User).filter(User.email == "test@example.com").first()

    goal = Goal(
        title="Test Goal for Review",
        description="Test Description",
        expected_result="Test Result",
        deadline=datetime.now() + timedelta(days=30),
        employee_id=user.id,
    )
    db_session.add(goal)
    db_session.commit()

    review_data = {
        "goal_id": goal.id,
        "review_type": "self",
        "answers": [{"question_id": "q1", "answer": "Test answer", "score": 4.5}],
    }

    response = client.post("/api/v1/reviews/", json=review_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == goal.id
    assert data["review_type"] == "self"
    assert data["calculated_score"] is not None
