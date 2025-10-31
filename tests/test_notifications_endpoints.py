from app.models.database import User, Notification


class TestNotificationsEndpoints:

    def test_mark_notification_read(self, client, auth_headers, db_session):
        """Тест отметки уведомления как прочитанного"""
        user = db_session.query(User).filter(User.email == "test@example.com").first()

        notification = Notification(
            user_id=user.id,
            title="Test Notification",
            message="Test message",
            notification_type="test_type",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()

        notification_id = notification.id

        response = client.put(
            f"/api/v1/notifications/{notification_id}/read", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Notification marked as read"

        from app.database.session import get_db

        fresh_db = next(get_db())

        try:
            updated_notification = (
                fresh_db.query(Notification)
                .filter(Notification.id == notification_id)
                .first()
            )

            assert updated_notification.is_read == True  # type: ignore
        finally:
            fresh_db.close()

    def test_mark_notification_read_simple(self, client, auth_headers, db_session):
        """Упрощенный тест отметки уведомления как прочитанного"""
        user = db_session.query(User).filter(User.email == "test@example.com").first()

        # Создаем уведомление
        notification = Notification(
            user_id=user.id,
            title="Test",
            message="Test",
            notification_type="test",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()

        notification_id = notification.id

        # Вызываем API
        response = client.put(
            f"/api/v1/notifications/{notification_id}/read", headers=auth_headers
        )

        # Проверяем ответ
        assert response.status_code == 200

        # Используем свежую сессию для проверки
        from app.database.session import get_db

        fresh_db = next(get_db())

        try:
            # Проверяем что уведомление существует и прочитано
            notification_check = (
                fresh_db.query(Notification)
                .filter(
                    Notification.id == notification_id, Notification.user_id == user.id
                )
                .first()
            )

            assert notification_check is not None
            assert notification_check.is_read == True  # type: ignore
        finally:
            fresh_db.close()

    def test_get_my_notifications(self, client, auth_headers, db_session):
        """Тест получения уведомлений пользователя"""
        user = db_session.query(User).filter(User.email == "test@example.com").first()

        # Создаем тестовые уведомления
        notification1 = Notification(
            user_id=user.id,
            title="Test Notification 1",
            message="Test message 1",
            notification_type="test_type",
        )
        notification2 = Notification(
            user_id=user.id,
            title="Test Notification 2",
            message="Test message 2",
            notification_type="test_type",
        )
        db_session.add_all([notification1, notification2])
        db_session.commit()

        response = client.get("/api/v1/notifications/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_my_notifications_unread_only(self, client, auth_headers, db_session):
        """Тест получения только непрочитанных уведомлений"""
        user = db_session.query(User).filter(User.email == "test@example.com").first()

        # Создаем уведомления с разным статусом
        notification1 = Notification(
            user_id=user.id,
            title="Unread Notification",
            message="Unread message",
            notification_type="test_type",
            is_read=False,
        )
        notification2 = Notification(
            user_id=user.id,
            title="Read Notification",
            message="Read message",
            notification_type="test_type",
            is_read=True,
        )
        db_session.add_all([notification1, notification2])
        db_session.commit()

        response = client.get(
            "/api/v1/notifications/?unread_only=true", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Проверяем что только непрочитанные
        assert all(not n["is_read"] for n in data)

    def test_mark_all_notifications_read(self, client, auth_headers, db_session):
        """Тест отметки всех уведомлений как прочитанных"""
        user = db_session.query(User).filter(User.email == "test@example.com").first()

        # Сначала отмечаем все существующие как прочитанные
        db_session.query(Notification).filter(Notification.user_id == user.id).update(
            {"is_read": True}
        )
        db_session.commit()

        # Создаем несколько непрочитанных уведомлений
        for i in range(3):
            notification = Notification(
                user_id=user.id,
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type="test_type",
                is_read=False,
            )
            db_session.add(notification)
        db_session.commit()

        # Получаем количество непрочитанных до
        unread_before = (
            db_session.query(Notification)
            .filter(Notification.user_id == user.id, Notification.is_read == False)
            .count()
        )
        assert unread_before == 3

        response = client.put("/api/v1/notifications/read-all", headers=auth_headers)

        assert response.status_code == 200
        assert "Marked 3 notifications as read" in response.json()["message"]

        # Используем свежую сессию для проверки
        from app.database.session import get_db

        fresh_db = next(get_db())

        try:
            # Проверяем что все прочитаны
            unread_after = (
                fresh_db.query(Notification)
                .filter(Notification.user_id == user.id, Notification.is_read == False)
                .count()
            )
            assert unread_after == 0
        finally:
            fresh_db.close()

    def test_get_unread_count(self, client, auth_headers, db_session):
        """Тест получения количества непрочитанных уведомлений"""
        user = db_session.query(User).filter(User.email == "test@example.com").first()

        # Очищаем старые уведомления
        db_session.query(Notification).filter(Notification.user_id == user.id).delete()
        db_session.commit()

        # Создаем уведомления
        notification1 = Notification(
            user_id=user.id,
            title="Unread 1",
            message="Message 1",
            notification_type="test_type",
            is_read=False,
        )
        notification2 = Notification(
            user_id=user.id,
            title="Unread 2",
            message="Message 2",
            notification_type="test_type",
            is_read=False,
        )
        db_session.add_all([notification1, notification2])
        db_session.commit()

        response = client.get(
            "/api/v1/notifications/unread-count", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["unread_count"] == 2

    def test_mark_notification_read_not_found(self, client, auth_headers):
        """Тест попытки отметить несуществующее уведомление"""
        response = client.put(
            "/api/v1/notifications/non-existent-id/read", headers=auth_headers
        )

        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]
