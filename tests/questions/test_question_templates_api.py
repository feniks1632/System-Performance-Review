from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.database.session import SessionLocal
from app.main import app
from app.models.database import User


client = TestClient(app)


def test_create_question_template():
    """Тест создания шаблона вопроса через API"""

    # 1. Сначала создаем тестового менеджера (если нет)
    db = SessionLocal()
    try:
        # Создаем тестового менеджера
        manager = User(
            email="manager@test.com",
            full_name="Test Manager",
            hashed_password=get_password_hash("password123"),
            is_manager=True,
        )
        db.add(manager)
        db.commit()
        db.refresh(manager)

        # 2. Логинимся как менеджер
        login_data = {"email": "manager@test.com", "password": "password123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 3. Создаем шаблон вопроса
        question_data = {
            "question_text": "Тестовый вопрос для самооценки",
            "question_type": "self",
            "section": "performance",
            "weight": 1.5,
            "max_score": 10,
            "order_index": 1,
            "trigger_words": '["тест", "проверка"]',
        }

        response = client.post(
            "/api/v1/question-templates/", json=question_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["question_text"] == question_data["question_text"]
        assert data["question_type"] == question_data["question_type"]
        assert data["weight"] == question_data["weight"]
        assert data["is_active"] == True

    finally:
        db.rollback()
        db.close()


def test_get_question_templates():
    """Тест получения списка шаблонов вопросов"""

    # Логинимся как обычный пользователь
    user_data = {"email": "user@test.com", "password": "password123"}

    # Создаем тестового пользователя
    db = SessionLocal()
    try:
        user = User(
            email="user@test.com",
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            is_manager=False,
        )
        db.add(user)
        db.commit()

        response = client.post("/api/v1/auth/login", json=user_data)
        assert response.status_code == 200
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Получаем список шаблонов
        response = client.get("/api/v1/question-templates/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    test_create_question_template()
    test_get_question_templates()
