from datetime import datetime, timedelta
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

@pytest.fixture
def test_question_templates(db_session):
    """Создает тестовые шаблоны вопросов"""
    from app.models.database import QuestionTemplate
    
    # Очищаем существующие вопросы
    db_session.query(QuestionTemplate).delete()
    
    questions_data = [
        # Самооценка
        {
            "question_text": "Опишите, каких результатов вы достигли по поставленной цели",
            "question_type": "self", 
            "section": "performance",
            "weight": 1.5,
            "max_score": 5,
            "trigger_words": '["достижен", "результат", "успех", "выполнен"]'
        },
        {
            "question_text": "Какие сложности возникли в процессе работы и как вы их преодолели?",
            "question_type": "self",
            "section": "problem_solving", 
            "weight": 1.2,
            "max_score": 5,
            "trigger_words": '["сложн", "проблем", "трудн", "преодолел"]'
        },
        
        # Оценка руководителя
        {
            "question_text": "Насколько сотрудник достиг запланированных результатов по цели?",
            "question_type": "manager",
            "section": "performance",
            "weight": 2.0,
            "max_score": 10,
            "trigger_words": '["результат", "достижен", "план", "KPI"]'
        },
        {
            "question_text": "Оцените качество взаимодействия сотрудника с коллегами",
            "question_type": "manager", 
            "section": "communication",
            "weight": 1.5,
            "max_score": 10,
            "trigger_words": '["коммуникац", "общен", "команд", "взаимодейств"]'
        },
    ]
    
    questions = []
    for i, q_data in enumerate(questions_data):
        question = QuestionTemplate(
            question_text=q_data["question_text"],
            question_type=q_data["question_type"],
            section=q_data["section"],
            weight=q_data["weight"],
            max_score=q_data["max_score"],
            trigger_words=q_data["trigger_words"],
            order_index=i
        )
        questions.append(question)
    
    db_session.add_all(questions)
    db_session.commit()
    
    return questions

@pytest.fixture
def test_employee_user(db_session):
    """Создает тестового сотрудника"""
    from app.core.security import get_password_hash
    from app.models.database import User

    employee = User(
        email="employee1@company.com",
        full_name="Алексей Козлов (Сотрудник)",
        hashed_password=get_password_hash("password123"), 
        is_manager=False
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

@pytest.fixture
def test_manager_user_complete(db_session):
    """Создает тестового руководителя с правильными данными"""
    from app.core.security import get_password_hash
    from app.models.database import User

    manager = User(
        email="manager1@company.com",
        full_name="Иван Петров (Руководитель)",
        hashed_password=get_password_hash("password123"),
        is_manager=True
    )
    db_session.add(manager)
    db_session.commit()
    db_session.refresh(manager)
    return manager

@pytest.fixture
def test_goal_with_employee(db_session, test_employee_user):
    """Создает тестовую цель для сотрудника"""
    from app.models.database import Goal
    
    future_date = datetime.now() + timedelta(days=90)
    
    goal = Goal(
        title="Разработка нового функционала системы",
        description="Реализация модуля аналитики и отчетности в Performance Review System",
        expected_result="Запущенный в продакшен модуль с полным покрытием требований",
        deadline=future_date,
        task_link="https://jira.company.com/TASK-123",
        employee_id=test_employee_user.id,
        status="active"
    )
    
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    
    return goal

@pytest.fixture
def employee_auth_headers(client, test_employee_user):
    """Заголовки аутентификации для сотрудника"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "employee1@company.com", "password": "password123"},
    )
    assert login_response.status_code == 200, f"Ошибка логина сотрудника: {login_response.text}"
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def manager_auth_headers(client, test_manager_user_complete):
    """Заголовки аутентификации для руководителя"""
    login_response = client.post(
        "/api/v1/auth/login", 
        json={"email": "manager1@company.com", "password": "password123"},
    )
    assert login_response.status_code == 200, f"Ошибка логина руководителя: {login_response.text}"
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}