# tests/test_user_service.py
import pytest
from app.core.security import get_password_hash
from app.services.user_service import UserService
from app.models.database import User


class TestUserService:

    def test_get_user_manager(self, user_service, db_session):
        """Тест получения руководителя пользователя"""
        manager = User(
            email="manager@example.com",
            full_name="Test Manager",
            hashed_password=get_password_hash("test"),
            is_manager=True,
        )
        employee = User(
            email="employee@example.com",
            full_name="Test Employee",
            hashed_password=get_password_hash("test"),
            is_manager=False,
            manager_id=manager.id,
        )
        db_session.add(manager)
        db_session.commit()  # Сначала сохраняем менеджера чтобы получить ID

        employee.manager_id = manager.id  # Теперь назначаем manager_id
        db_session.add(employee)
        db_session.commit()

        found_manager = user_service.get_user_manager(employee.id)

        assert found_manager is not None
        assert found_manager.id == manager.id

    def test_get_user_manager_no_manager(self, user_service, db_session):
        """Тест получения руководителя когда его нет"""
        employee = User(
            email="employee@example.com",
            full_name="Test Employee",
            hashed_password=get_password_hash("test"),
            is_manager=False,
        )
        db_session.add(employee)
        db_session.commit()

        manager = user_service.get_user_manager(employee.id)

        assert manager is None

    def test_get_user_subordinates(self, user_service, db_session):
        """Тест получения подчиненных руководителя"""
        manager = User(
            email="manager@example.com",
            full_name="Test Manager",
            hashed_password=get_password_hash("test"),
            is_manager=True,
        )
        db_session.add(manager)
        db_session.commit()  # Сначала сохраняем менеджера

        employee1 = User(
            email="employee1@example.com",
            full_name="Employee 1",
            hashed_password=get_password_hash("test"),
            is_manager=False,
            manager_id=manager.id,
        )
        employee2 = User(
            email="employee2@example.com",
            full_name="Employee 2",
            hashed_password=get_password_hash("test"),
            is_manager=False,
            manager_id=manager.id,
        )
        db_session.add_all([employee1, employee2])
        db_session.commit()

        subordinates = user_service.get_user_subordinates(manager.id)

        assert len(subordinates) == 2
        assert all(emp.manager_id == manager.id for emp in subordinates)

    def test_get_all_managers(self, user_service, db_session):
        """Тест получения всех руководителей"""
        manager1 = User(
            email="manager1@example.com",
            full_name="Manager 1",
            hashed_password=get_password_hash("test"),
            is_manager=True,
        )
        manager2 = User(
            email="manager2@example.com",
            full_name="Manager 2",
            hashed_password=get_password_hash("test"),
            is_manager=True,
        )
        employee = User(
            email="employee@example.com",
            full_name="Employee",
            hashed_password=get_password_hash("test"),
            is_manager=False,
        )
        db_session.add_all([manager1, manager2, employee])
        db_session.commit()

        managers = user_service.get_all_managers()

        assert len(managers) == 2
        assert all(manager.is_manager for manager in managers)

    def test_assign_manager(self, user_service, db_session):
        """Тест назначения руководителя сотруднику"""
        manager = User(
            email="manager@example.com",
            full_name="Test Manager",
            hashed_password=get_password_hash("test"),
            is_manager=True,
        )
        employee = User(
            email="employee@example.com",
            full_name="Test Employee",
            hashed_password=get_password_hash("test"),
            is_manager=False,
        )
        db_session.add_all([manager, employee])
        db_session.commit()

        success = user_service.assign_manager(employee.id, manager.id)

        assert success is True

        # Проверяем что руководитель назначен
        updated_employee = db_session.query(User).filter(User.id == employee.id).first()
        assert updated_employee.manager_id == manager.id

    def test_assign_manager_not_manager(self, user_service, db_session):
        """Тест назначения не-руководителя как руководителя"""
        not_manager = User(
            email="notmanager@example.com",
            full_name="Not Manager",
            hashed_password=get_password_hash("test"),
            is_manager=False,
        )
        employee = User(
            email="employee@example.com",
            full_name="Test Employee",
            hashed_password=get_password_hash("test"),
            is_manager=False,
        )
        db_session.add_all([not_manager, employee])
        db_session.commit()

        success = user_service.assign_manager(employee.id, not_manager.id)

        assert success is False

    def test_assign_manager_user_not_found(self, user_service, db_session):
        """Тест назначения руководителя несуществующему пользователю"""
        manager = User(
            email="manager@example.com",
            full_name="Test Manager",
            hashed_password=get_password_hash("test"),
            is_manager=True,
        )
        db_session.add(manager)
        db_session.commit()

        success = user_service.assign_manager("non-existent-id", manager.id)

        assert success is False
