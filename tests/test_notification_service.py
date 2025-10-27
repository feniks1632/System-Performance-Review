# tests/test_notification_service.py
import pytest
from datetime import datetime, timedelta
from app.services.notification_service import NotificationService
from app.models.database import User, Notification


class TestNotificationService:

    def test_create_notification(self, notification_service, db_session):
        """Тест создания уведомления"""
        # Создаем тестового пользователя
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        # Создаем уведомление
        notification = notification_service.create_notification(
            user_id=user.id,
            title="Test Title",
            message="Test Message",
            notification_type="test_type",
            related_entity_type="goal",
            related_entity_id="goal-123",
        )

        assert notification.id is not None
        assert notification.title == "Test Title"
        assert notification.message == "Test Message"
        assert notification.notification_type == "test_type"
        assert notification.user_id == user.id
        assert notification.is_read == False

    def test_get_user_notifications(self, notification_service, db_session):
        """Тест получения уведомлений пользователя"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        # Создаем несколько уведомлений
        for i in range(3):
            notification_service.create_notification(
                user_id=user.id,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="test_type",
            )

        # Получаем уведомления
        notifications = notification_service.get_user_notifications(user.id)

        assert len(notifications) == 3
        assert notifications[0].title == "Notification 2"  # Последнее первое

    def test_get_user_notifications_unread_only(self, notification_service, db_session):
        """Тест получения только непрочитанных уведомлений"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        # Создаем прочитанные и непрочитанные уведомления
        notification1 = notification_service.create_notification(
            user_id=user.id,
            title="Unread",
            message="Unread message",
            notification_type="test_type",
        )

        notification2 = notification_service.create_notification(
            user_id=user.id,
            title="Read",
            message="Read message",
            notification_type="test_type",
        )

        # Отмечаем второе как прочитанное
        notification_service.mark_as_read(notification2.id, user.id)

        # Получаем только непрочитанные
        unread_notifications = notification_service.get_user_notifications(
            user.id, unread_only=True
        )

        assert len(unread_notifications) == 1
        assert unread_notifications[0].title == "Unread"

    def test_mark_as_read(self, notification_service, db_session):
        """Тест отметки уведомления как прочитанного"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        notification = notification_service.create_notification(
            user_id=user.id, title="Test", message="Test", notification_type="test_type"
        )

        # Отмечаем как прочитанное
        success = notification_service.mark_as_read(notification.id, user.id)

        assert success is True

        # Проверяем что уведомление прочитано
        updated_notification = (
            db_session.query(Notification)
            .filter(Notification.id == notification.id)
            .first()
        )
        assert updated_notification.is_read == True

    def test_mark_as_read_wrong_user(self, notification_service, db_session):
        """Тест попытки отметить чужое уведомление"""
        user1 = User(
            email="user1@example.com",
            full_name="User 1",
            hashed_password="test",
            is_manager=False,
        )
        user2 = User(
            email="user2@example.com",
            full_name="User 2",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        notification = notification_service.create_notification(
            user_id=user1.id,
            title="Test",
            message="Test",
            notification_type="test_type",
        )

        # Пытаемся отметить уведомление другого пользователя
        success = notification_service.mark_as_read(notification.id, user2.id)

        assert success is False

    def test_mark_all_as_read(self, notification_service, db_session):
        """Тест отметки всех уведомлений как прочитанных"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        # Создаем несколько непрочитанных уведомлений
        for i in range(3):
            notification_service.create_notification(
                user_id=user.id,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="test_type",
            )

        # Отмечаем все как прочитанные
        count = notification_service.mark_all_as_read(user.id)

        assert count == 3

        # Проверяем что все прочитаны
        unread_count = notification_service.get_unread_count(user.id)
        assert unread_count == 0

    def test_get_unread_count(self, notification_service, db_session):
        """Тест получения количества непрочитанных уведомлений"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(user)
        db_session.commit()

        # Создаем уведомления
        for i in range(2):
            notification_service.create_notification(
                user_id=user.id,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="test_type",
            )

        # Отмечаем одно как прочитанное
        notifications = notification_service.get_user_notifications(user.id)
        notification_service.mark_as_read(notifications[0].id, user.id)

        # Проверяем количество непрочитанных
        unread_count = notification_service.get_unread_count(user.id)
        assert unread_count == 1

    def test_create_review_pending_notification(self, notification_service, db_session):
        """Тест создания уведомления о ожидающем ревью"""
        manager = User(
            email="manager@example.com",
            full_name="Test Manager",
            hashed_password="test",
            is_manager=True,
        )
        db_session.add(manager)
        db_session.commit()

        notification = notification_service.create_review_pending_notification(
            goal_id="goal-123", employee_name="Test Employee", manager_id=manager.id
        )

        assert notification.title == "Ожидает ревью"
        assert "Test Employee" in notification.message
        assert notification.notification_type == "review_pending"
        assert notification.related_entity_type == "goal"

    def test_create_goal_created_notification(self, notification_service, db_session):
        """Тест создания уведомлений о новой цели"""
        respondent1 = User(
            email="resp1@example.com",
            full_name="Respondent 1",
            hashed_password="test",
            is_manager=False,
        )
        respondent2 = User(
            email="resp2@example.com",
            full_name="Respondent 2",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add_all([respondent1, respondent2])
        db_session.commit()

        notifications = notification_service.create_goal_created_notification(
            goal_id="goal-123",
            employee_name="Test Employee",
            respondent_ids=[respondent1.id, respondent2.id],
        )

        assert len(notifications) == 2
        assert all(n.title == "Новая цель для оценки" for n in notifications)
        assert all("Test Employee" in n.message for n in notifications)

    def test_create_review_completed_notification(
        self, notification_service, db_session
    ):
        """Тест создания уведомления о завершении ревью"""
        employee = User(
            email="employee@example.com",
            full_name="Test Employee",
            hashed_password="test",
            is_manager=False,
        )
        db_session.add(employee)
        db_session.commit()

        notification = notification_service.create_review_completed_notification(
            goal_id="goal-123", manager_name="Test Manager", employee_id=employee.id
        )

        assert notification.title == "Ревью завершено"
        assert "Test Manager" in notification.message
        assert notification.notification_type == "review_completed"
