import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import engine, get_db
from app.models.database import Base
from sqlalchemy import text
from unittest.mock import MagicMock, patch
from app.services.email_service import EmailService


@pytest.fixture(scope="function")
def client():
    """Тестовый клиент с очисткой базы между тестами"""
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()

    return TestClient(app)


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "full_name": "Тестовый Пользователь",
        "password": "testpass123",
        "is_manager": False,
    }


@pytest.fixture
def test_manager_data():
    return {
        "email": "manager@example.com",
        "full_name": "Тестовый Руководитель",
        "password": "testpass123",
        "is_manager": True,
    }


@pytest.fixture
def auth_headers(client, test_user_data, db_session):
    """Фикстура для получения заголовков аутентификации"""
    from app.core.security import get_password_hash
    from app.models.database import User

    # Создаем пользователя с правильным хешем пароля
    user_data = test_user_data.copy()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

    # Создаем пользователя напрямую в БД используя db_session
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Логинимся
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_manager_user(db_session):
    """Создает тестового менеджера с правильным хешем пароля"""
    from app.core.security import get_password_hash
    from app.models.database import User

    manager = User(
        email="manager@test.com",
        full_name="Test Manager",
        hashed_password=get_password_hash("testpass123"),
        is_manager=True,
    )
    db_session.add(manager)
    db_session.commit()
    return manager


@pytest.fixture
def analytics_service(db_session):
    """Фикстура для сервиса аналитики"""
    from app.services.analytics_service import AnalyticsService

    return AnalyticsService(db_session)


@pytest.fixture
def db_session():
    """Фикстура для сессии базы данных"""
    from app.database.session import get_db

    db = next(get_db())

    # Очищаем базу перед каждым тестом
    with db.bind.connect() as conn:  # type: ignore
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def email_service(db_session):
    """Фикстура для сервиса email"""
    return EmailService(db_session)


@pytest.fixture
def mock_smtp():
    """Mock для SMTP с улучшенной диагностикой"""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = MagicMock()

        # Сохраняем отправленные сообщения для проверки
        mock_instance.sent_messages = []

        def capture_send_message(msg):
            mock_instance.sent_messages.append(msg)
            return True

        mock_instance.send_message.side_effect = capture_send_message
        mock_smtp.return_value.__enter__.return_value = mock_instance

        yield mock_smtp, mock_instance


@pytest.fixture
def test_goal_data():
    return {
        "title": "Тестовая цель",
        "description": "Описание тестовой цели",
        "expected_result": "Ожидаемый результат",
        "deadline": "2024-12-31T00:00:00",
        "task_link": "https://example.com/task/1",
    }


@pytest.fixture
def create_test_goal(client, auth_headers, test_goal_data):
    """Создает тестовую цель и возвращает ее ID"""
    response = client.post("/api/v1/goals/", json=test_goal_data, headers=auth_headers)
    return response.json()["id"]


@pytest.fixture
def notification_service(db_session):
    """Фикстура для сервиса уведомлений"""
    from app.services.notification_service import NotificationService

    return NotificationService(db_session)


@pytest.fixture
def user_service(db_session):
    """Фикстура для сервиса пользователей"""
    from app.services.user_service import UserService

    return UserService(db_session)
