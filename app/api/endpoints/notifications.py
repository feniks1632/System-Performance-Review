from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.endpoints.auth import get_current_user
from app.database.session import get_db
from app.models.database import User
from app.models.schemas import (
    NotificationResponse,
    UnreadCountResponse,
    SuccessResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])


@router.get(
    "/",
    response_model=List[NotificationResponse],
    summary="Мои уведомления",
    description="Получение списка уведомлений текущего пользователя",
)
async def get_my_notifications(
    unread_only: bool = Query(False, description="Только непрочитанные уведомления"),
    limit: int = Query(50, description="Количество уведомлений", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение уведомлений текущего пользователя"""
    notification_service = NotificationService(db)
    notifications = notification_service.get_user_notifications(
        user_id=current_user.id, limit=limit, unread_only=unread_only  # type: ignore
    )

    return notifications


@router.put(
    "/{notification_id}/read",
    response_model=SuccessResponse,
    summary="Отметить как прочитанное",
    description="Отметить уведомление как прочитанное",
)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отметить уведомление как прочитанное"""
    notification_service = NotificationService(db)
    success = notification_service.mark_as_read(notification_id, current_user.id)  # type: ignore

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return SuccessResponse(message="Notification marked as read")


@router.put(
    "/read-all",
    response_model=SuccessResponse,
    summary="Отметить все как прочитанные",
    description="Отметить все уведомления пользователя как прочитанные",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Отметить все уведомления как прочитанные"""
    notification_service = NotificationService(db)
    count = notification_service.mark_all_as_read(current_user.id)  # type: ignore

    return SuccessResponse(message=f"Marked {count} notifications as read")


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Количество непрочитанных",
    description="Количество непрочитанных уведомлений пользователя",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить количество непрочитанных уведомлений"""
    notification_service = NotificationService(db)
    count = notification_service.get_unread_count(current_user.id)  # type: ignore

    return UnreadCountResponse(unread_count=count)
