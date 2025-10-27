# tests/test_users_endpoints.py
import pytest
from app.core.security import get_password_hash
from app.models.database import User


class TestUsersEndpoints:

    def test_get_all_managers_as_manager(self, client, db_session):
        """Тест получения списка руководителей (руководителем)"""
        # Создаем менеджера с правильным паролем
        manager = User(
            email="manager_user@test.com",
            full_name="Test Manager",
            hashed_password=get_password_hash("managerpass123"),
            is_manager=True,
        )
        db_session.add(manager)
        db_session.commit()

        # Логинимся как менеджер
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "manager_user@test.com", "password": "managerpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        manager_headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/users/managers", headers=manager_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(user["email"] == "manager_user@test.com" for user in data)

    def test_get_all_managers_as_employee(self, client, auth_headers):
        """Тест получения списка руководителей (сотрудником) - должен быть запрещен"""
        response = client.get("/api/v1/users/managers", headers=auth_headers)

        assert response.status_code == 403
        assert "Only managers can view managers list" in response.json()["detail"]

    def test_get_my_subordinates_as_manager(self, client, db_session):
        """Тест получения подчиненных (руководителем)"""
        # Создаем менеджера с подчиненными
        manager = User(
            email="manager_with_subs@test.com",
            full_name="Manager With Subs",
            hashed_password=get_password_hash("managerpass123"),
            is_manager=True,
        )
        db_session.add(manager)
        db_session.commit()

        employee1 = User(
            email="subordinate1@test.com",
            full_name="Subordinate 1",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
            manager_id=manager.id,
        )
        employee2 = User(
            email="subordinate2@test.com",
            full_name="Subordinate 2",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
            manager_id=manager.id,
        )
        db_session.add_all([employee1, employee2])
        db_session.commit()

        # Логинимся как менеджер
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "manager_with_subs@test.com", "password": "managerpass123"},
        )
        token = login_response.json()["access_token"]
        manager_headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/users/my-subordinates", headers=manager_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Проверяем что пользователи возвращаются и они подчиненные
        # Получаем реальные данные из БД для проверки
        subordinates_from_db = (
            db_session.query(User).filter(User.manager_id == manager.id).all()
        )
        subordinate_emails = [emp.email for emp in subordinates_from_db]

        for emp in data:
            assert emp["email"] in subordinate_emails

    def test_get_my_subordinates_as_employee(self, client, auth_headers):
        """Тест получения подчиненных (сотрудником) - должен быть запрещен"""
        response = client.get("/api/v1/users/my-subordinates", headers=auth_headers)

        assert response.status_code == 403
        assert "Only managers can view subordinates" in response.json()["detail"]

    def test_assign_manager(self, client, db_session):
        """Тест назначения руководителя сотруднику"""
        manager = User(
            email="assign_manager@test.com",
            full_name="Assign Manager",
            hashed_password=get_password_hash("managerpass123"),
            is_manager=True,
        )
        employee = User(
            email="employee_to_assign@test.com",
            full_name="Employee To Assign",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
        )
        db_session.add_all([manager, employee])
        db_session.commit()

        # Логинимся как менеджер
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "assign_manager@test.com", "password": "managerpass123"},
        )
        token = login_response.json()["access_token"]
        manager_headers = {"Authorization": f"Bearer {token}"}

        # правильный формат запроса для PUT с query параметрами
        response = client.put(
            f"/api/v1/users/{employee.id}/manager?manager_id={manager.id}",
            headers=manager_headers,
        )

        assert response.status_code == 200
        assert "Manager assigned successfully" in response.json()["message"]

    def test_assign_manager_as_employee(self, client, auth_headers, db_session):
        """Тест назначения руководителя сотрудником - должен быть запрещен"""
        manager = User(
            email="manager_for_assign@test.com",
            full_name="Manager For Assign",
            hashed_password=get_password_hash("managerpass123"),
            is_manager=True,
        )
        employee = User(
            email="employee_assigner@test.com",
            full_name="Employee Assigner",
            hashed_password=get_password_hash("testpass123"),
            is_manager=False,
        )
        db_session.add_all([manager, employee])
        db_session.commit()

        response = client.put(
            f"/api/v1/users/{employee.id}/manager?manager_id={manager.id}",
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "Only managers can assign managers" in response.json()["detail"]
