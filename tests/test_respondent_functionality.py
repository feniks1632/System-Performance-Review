import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestRespondentFunctionalityFinal:
    """Финальные тесты функционала респондентов с исправлениями"""

    def test_respondent_can_access_assigned_goals(
        self, client, test_employee_user, db_session
    ):
        """Тест: Респондент может получить цели, где он назначен"""
        # Регистрируем респондента через API
        registration_data = {
            "email": "respondent_final@test.com",
            "full_name": "Тест Респондент Финальный",
            "password": "password123",
            "is_manager": False,
        }
        registration_response = client.post(
            "/api/v1/auth/register", json=registration_data
        )
        assert registration_response.status_code == 200
        respondent_id = registration_response.json()["id"]

        # Логинимся как сотрудник для создания цели
        employee_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_employee_user.email,
                "password": "password123",  # ПРАВИЛЬНЫЙ ПАРОЛЬ
            },
        )
        assert (
            employee_login.status_code == 200
        ), f"Employee login failed: {employee_login.text}"
        employee_headers = {
            "Authorization": f"Bearer {employee_login.json()['access_token']}"
        }

        # Создаем цель через API с респондентом
        future_date = datetime.now() + timedelta(days=90)
        goal_data = {
            "title": "Тестовая цель с респондентом",
            "description": "Описание цели",
            "expected_result": "Ожидаемый результат",
            "deadline": future_date.isoformat(),
            "respondent_ids": [respondent_id],
        }
        goal_response = client.post(
            "/api/v1/goals/", json=goal_data, headers=employee_headers
        )
        assert (
            goal_response.status_code == 200
        ), f"Goal creation failed: {goal_response.text}"
        goal_id = goal_response.json()["id"]

        # Логинимся как респондент
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "respondent_final@test.com", "password": "password123"},
        )
        assert (
            login_response.status_code == 200
        ), f"Respondent login failed: {login_response.text}"
        respondent_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Респондент получает свои цели
        response = client.get("/api/v1/goals/respondent/my", headers=respondent_headers)

        assert response.status_code == 200, f"Get goals failed: {response.text}"
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == goal_id
        assert data[0]["title"] == "Тестовая цель с респондентом"

    def test_respondent_can_get_specific_goal(
        self, client, test_employee_user, db_session
    ):
        """Тест: Респондент может получить конкретную цель"""
        # Регистрируем респондента через API
        registration_data = {
            "email": "respondent_specific@test.com",
            "full_name": "Тест Респондент Конкретный",
            "password": "password123",
            "is_manager": False,
        }
        registration_response = client.post(
            "/api/v1/auth/register", json=registration_data
        )
        assert registration_response.status_code == 200
        respondent_id = registration_response.json()["id"]

        # Логинимся как сотрудник
        employee_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_employee_user.email,
                "password": "password123",  # ПРАВИЛЬНЫЙ ПАРОЛЬ
            },
        )
        assert (
            employee_login.status_code == 200
        ), f"Employee login failed: {employee_login.text}"
        employee_headers = {
            "Authorization": f"Bearer {employee_login.json()['access_token']}"
        }

        # Создаем цель через API с респондентом
        future_date = datetime.now() + timedelta(days=90)
        goal_data = {
            "title": "Конкретная тестовая цель",
            "description": "Описание конкретной цели",
            "expected_result": "Конкретный результат",
            "deadline": future_date.isoformat(),
            "respondent_ids": [respondent_id],
        }
        goal_response = client.post(
            "/api/v1/goals/", json=goal_data, headers=employee_headers
        )
        assert (
            goal_response.status_code == 200
        ), f"Goal creation failed: {goal_response.text}"
        goal_id = goal_response.json()["id"]

        # Логинимся как респондент
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "respondent_specific@test.com", "password": "password123"},
        )
        assert (
            login_response.status_code == 200
        ), f"Respondent login failed: {login_response.text}"
        respondent_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Респондент получает конкретную цель
        response = client.get(
            f"/api/v1/goals/respondent/{goal_id}", headers=respondent_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == goal_id
        assert data["title"] == "Конкретная тестовая цель"

    def test_respondent_can_get_goal_steps(
        self, client, test_employee_user, db_session
    ):
        """Тест: Респондент может получить подпункты цели"""
        # Регистрируем респондента через API
        registration_data = {
            "email": "respondent_steps@test.com",
            "full_name": "Тест Респондент Подпункты",
            "password": "password123",
            "is_manager": False,
        }
        registration_response = client.post(
            "/api/v1/auth/register", json=registration_data
        )
        assert registration_response.status_code == 200
        respondent_id = registration_response.json()["id"]

        # Логинимся как сотрудник
        employee_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_employee_user.email,
                "password": "password123",  # ПРАВИЛЬНЫЙ ПАРОЛЬ
            },
        )
        assert (
            employee_login.status_code == 200
        ), f"Employee login failed: {employee_login.text}"
        employee_headers = {
            "Authorization": f"Bearer {employee_login.json()['access_token']}"
        }

        # Создаем цель с подпунктами через API
        future_date = datetime.now() + timedelta(days=90)
        goal_data = {
            "title": "Цель с подпунктами",
            "description": "Описание цели с подпунктами",
            "expected_result": "Результат с подпунктами",
            "deadline": future_date.isoformat(),
            "respondent_ids": [respondent_id],
            "steps": [
                {
                    "title": "Первый шаг",
                    "description": "Описание первого шага",
                    "order_index": 0,
                },
                {
                    "title": "Второй шаг",
                    "description": "Описание второго шага",
                    "order_index": 1,
                },
            ],
        }
        goal_response = client.post(
            "/api/v1/goals/", json=goal_data, headers=employee_headers
        )
        assert (
            goal_response.status_code == 200
        ), f"Goal creation failed: {goal_response.text}"
        goal_id = goal_response.json()["id"]

        # Логинимся как респондент
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "respondent_steps@test.com", "password": "password123"},
        )
        assert (
            login_response.status_code == 200
        ), f"Respondent login failed: {login_response.text}"
        respondent_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Респондент получает подпункты через специальный эндпоинт
        response = client.get(
            f"/api/v1/respondent/{goal_id}/steps", headers=respondent_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Первый шаг"
        assert data[1]["title"] == "Второй шаг"

    def test_respondent_can_use_regular_endpoints(
        self, client, test_employee_user, db_session
    ):
        """Тест: Респондент может использовать обычные эндпоинты"""
        # Регистрируем респондента через API
        registration_data = {
            "email": "respondent_regular@test.com",
            "full_name": "Тест Респондент Обычный",
            "password": "password123",
            "is_manager": False,
        }
        registration_response = client.post(
            "/api/v1/auth/register", json=registration_data
        )
        assert registration_response.status_code == 200
        respondent_id = registration_response.json()["id"]

        # Логинимся как сотрудник
        employee_login = client.post(
            "/api/v1/auth/login",
            json={"email": test_employee_user.email, "password": "password123"},
        )
        assert (
            employee_login.status_code == 200
        ), f"Employee login failed: {employee_login.text}"
        employee_headers = {
            "Authorization": f"Bearer {employee_login.json()['access_token']}"
        }

        # Создаем цель через API с респондентом
        future_date = datetime.now() + timedelta(days=90)
        goal_data = {
            "title": "Цель для обычных эндпоинтов",
            "description": "Описание цели",
            "expected_result": "Ожидаемый результат",
            "deadline": future_date.isoformat(),
            "respondent_ids": [respondent_id],
        }
        goal_response = client.post(
            "/api/v1/goals/", json=goal_data, headers=employee_headers
        )
        assert (
            goal_response.status_code == 200
        ), f"Goal creation failed: {goal_response.text}"
        goal_id = goal_response.json()["id"]

        # Логинимся как респондент
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "respondent_regular@test.com", "password": "password123"},
        )
        assert (
            login_response.status_code == 200
        ), f"Respondent login failed: {login_response.text}"
        respondent_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Респондент использует обычный эндпоинт для получения цели
        response = client.get(f"/api/v1/goals/{goal_id}", headers=respondent_headers)

        assert response.status_code == 200
        data = response.json()
        # Добавим проверку типа данных
        assert isinstance(data, dict), f"Expected dict, got {type(data)}: {data}"
        assert data["id"] == goal_id

        # Респондент использует обычный эндпоинт для получения подпунктов
        response = client.get(
            f"/api/v1/goals/{goal_id}/steps", headers=respondent_headers
        )

        assert response.status_code == 200
        steps_data = response.json()
        # Проверим, что это список
        assert isinstance(
            steps_data, list
        ), f"Expected list, got {type(steps_data)}: {steps_data}"

    def test_stranger_cannot_access_goal(self, client, test_employee_user, db_session):
        """Тест: Посторонний не может получить доступ к цели"""
        # Регистрируем постороннего пользователя через API
        stranger_registration = {
            "email": "stranger_final@test.com",
            "full_name": "Посторонний Пользователь Финальный",
            "password": "password123",
            "is_manager": False,
        }
        stranger_response = client.post(
            "/api/v1/auth/register", json=stranger_registration
        )
        assert stranger_response.status_code == 200

        # Логинимся как сотрудник и создаем цель
        employee_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_employee_user.email,
                "password": "password123",  # ПРАВИЛЬНЫЙ ПАРОЛЬ
            },
        )
        assert (
            employee_login.status_code == 200
        ), f"Employee login failed: {employee_login.text}"
        employee_headers = {
            "Authorization": f"Bearer {employee_login.json()['access_token']}"
        }

        future_date = datetime.now() + timedelta(days=90)
        goal_data = {
            "title": "Цель без постороннего",
            "description": "Описание цели",
            "expected_result": "Ожидаемый результат",
            "deadline": future_date.isoformat(),
            "respondent_ids": [],  # Не добавляем постороннего
        }
        goal_response = client.post(
            "/api/v1/goals/", json=goal_data, headers=employee_headers
        )
        assert (
            goal_response.status_code == 200
        ), f"Goal creation failed: {goal_response.text}"
        goal_id = goal_response.json()["id"]

        # Логинимся как посторонний
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "stranger_final@test.com", "password": "password123"},
        )
        assert (
            login_response.status_code == 200
        ), f"Stranger login failed: {login_response.text}"
        stranger_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Посторонний пытается получить цель
        response = client.get(f"/api/v1/goals/{goal_id}", headers=stranger_headers)

        assert response.status_code == 403


def test_respondent_workflow_fixed(client, test_employee_user, db_session):
    """Исправленный комплексный тест workflow респондента"""
    # 1. Регистрируем респондента через API
    registration_data = {
        "email": "workflow_fixed@test.com",
        "full_name": "Респондент Workflow Исправленный",
        "password": "password123",
        "is_manager": False,
    }
    registration_response = client.post("/api/v1/auth/register", json=registration_data)
    assert registration_response.status_code == 200
    respondent_id = registration_response.json()["id"]

    # 2. Логинимся как сотрудник для создания цели
    employee_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_employee_user.email,
            "password": "password123",  # ПРАВИЛЬНЫЙ ПАРОЛЬ
        },
    )
    assert (
        employee_login.status_code == 200
    ), f"Employee login failed: {employee_login.text}"
    employee_headers = {
        "Authorization": f"Bearer {employee_login.json()['access_token']}"
    }

    # 3. Создаем цель с подпунктами через API
    future_date = datetime.now() + timedelta(days=90)
    goal_data = {
        "title": "Workflow цель исправленная",
        "description": "Описание workflow цели",
        "expected_result": "Workflow результат",
        "deadline": future_date.isoformat(),
        "respondent_ids": [respondent_id],
        "steps": [
            {
                "title": "Workflow шаг 1",
                "description": "Описание шага 1",
                "order_index": 0,
            },
            {
                "title": "Workflow шаг 2",
                "description": "Описание шага 2",
                "order_index": 1,
            },
        ],
    }
    goal_response = client.post(
        "/api/v1/goals/", json=goal_data, headers=employee_headers
    )
    assert (
        goal_response.status_code == 200
    ), f"Goal creation failed: {goal_response.text}"
    goal_id = goal_response.json()["id"]

    # 4. Логинимся как респондент
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "workflow_fixed@test.com",  # ИСПРАВЛЕННЫЙ EMAIL
            "password": "password123",
        },
    )
    assert (
        login_response.status_code == 200
    ), f"Respondent login failed: {login_response.text}"
    respondent_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # 5. Проверяем все эндпоинты для респондента

    # 5.1 Получаем список целей респондента
    response = client.get("/api/v1/goals/respondent/my", headers=respondent_headers)
    assert response.status_code == 200
    goals = response.json()
    assert len(goals) == 1
    assert goals[0]["title"] == "Workflow цель исправленная"

    # 5.2 Получаем конкретную цель как респондент
    response = client.get(
        f"/api/v1/goals/respondent/{goal_id}", headers=respondent_headers
    )
    assert response.status_code == 200
    goal_data = response.json()
    assert goal_data["title"] == "Workflow цель исправленная"

    # 5.3 Получаем подпункты через специальный эндпоинт
    response = client.get(
        f"/api/v1/respondent/{goal_id}/steps", headers=respondent_headers
    )
    assert response.status_code == 200
    steps = response.json()
    assert len(steps) == 2

    # 5.4 Используем обычные эндпоинты
    response = client.get(f"/api/v1/goals/{goal_id}", headers=respondent_headers)
    assert response.status_code == 200

    response = client.get(f"/api/v1/goals/{goal_id}/steps", headers=respondent_headers)
    assert response.status_code == 200

    print("✅ Весь workflow респондента работает корректно!")
