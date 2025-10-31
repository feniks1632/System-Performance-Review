from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.database import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
    ) -> Notification:
        """Создание нового уведомления"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        logger.info(f"Created notification for user {user_id}: {title}")
        return notification

    def get_user_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> List[Notification]:
        """Получение уведомлений пользователя"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifications = (
            query.order_by(Notification.created_at.desc()).limit(limit).all()
        )
        return notifications

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Отметить уведомление как прочитанное"""
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            return False

        notification.is_read = True  # type: ignore
        self.db.commit()
        return True

    def mark_all_as_read(self, user_id: str) -> int:
        """Отметить все уведомления пользователя как прочитанные"""
        result = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True})
        )

        self.db.commit()
        logger.info(f"Marked {result} notifications as read for user {user_id}")
        return result

    def get_unread_count(self, user_id: str) -> int:
        """Получить количество непрочитанных уведомлений"""
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

        return count

    def create_review_pending_notification(
        self, goal_id: str, employee_name: str, manager_id: str
    ):
        """Создание уведомления о необходимости пройти ревью"""
        return self.create_notification(
            user_id=manager_id,
            title="Ожидает ревью",
            message=f"Сотрудник {employee_name} завершил самооценку и ожидает вашего ревью",
            notification_type="review_pending",
            related_entity_type="goal",
            related_entity_id=goal_id,
        )

    def create_goal_created_notification(
        self, goal_id: str, employee_name: str, respondent_ids: List[str]
    ):
        """Создание уведомлений для респондентов о новой цели"""
        notifications = []
        for respondent_id in respondent_ids:
            notification = self.create_notification(
                user_id=respondent_id,
                title="Новая цель для оценки",
                message=f"Сотрудник {employee_name} создал новую цель и просит вашей оценки",
                notification_type="goal_created",
                related_entity_type="goal",
                related_entity_id=goal_id,
            )
            notifications.append(notification)

        return notifications

    def create_review_completed_notification(
        self, goal_id: str, manager_name: str, employee_id: str
    ):
        """Создание уведомления о завершении ревью"""
        return self.create_notification(
            user_id=employee_id,
            title="Ревью завершено",
            message=f"Ваш руководитель {manager_name} завершил оценку вашей работы",
            notification_type="review_completed",
            related_entity_type="goal",
            related_entity_id=goal_id,
        )
