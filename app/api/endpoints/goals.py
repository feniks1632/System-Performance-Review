from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.schemas import GoalCreate, GoalResponse
from app.models.database import Goal as GoalModel, User
from app.api.endpoints.auth import get_current_user
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["goals"])


@router.post(
    "/",
    response_model=GoalResponse,
    summary="Создание цели",
    description="""
    Создание новой цели для сотрудника.
    
    - **Максимум 5 целей на сотрудника**
    - **respondent_ids**: список ID пользователей, которые будут оценивать прогресс
    - **Автоматически отправляет уведомления респондентам**
    """,
)
async def create_goal(
    goal: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создание новой цели"""
    # Проверяем количество целей (максимум 5)
    existing_goals = (
        db.query(GoalModel).filter(GoalModel.employee_id == current_user.id).count()
    )

    if existing_goals >= 5:
        raise HTTPException(
            status_code=400, detail="Maximum 5 goals allowed per employee"
        )

    # Создаем цель
    db_goal = GoalModel(
        title=goal.title,
        description=goal.description,
        expected_result=goal.expected_result,
        deadline=goal.deadline,
        task_link=goal.task_link,
        employee_id=current_user.id,
    )

    # Добавляем респондентов если есть
    if goal.respondent_ids:
        respondents = db.query(User).filter(User.id.in_(goal.respondent_ids)).all()
        db_goal.respondents.extend(respondents)

    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)

    # СОЗДАЕМ IN-APP УВЕДОМЛЕНИЯ
    if goal.respondent_ids:
        notification_service = NotificationService(db)
        notification_service.create_goal_created_notification(
            goal_id=db_goal.id,  # type: ignore
            employee_name=current_user.full_name,  # type: ignore
            respondent_ids=goal.respondent_ids,
        )

        # АВТОМАТИЧЕСКАЯ ОТПРАВКА УВЕДОМЛЕНИЙ РЕСПОНДЕНТАМ
        respondent_emails = []
        for respondent_id in goal.respondent_ids:
            respondent = db.query(User).filter(User.id == respondent_id).first()
            if respondent and respondent.email:  # type: ignore
                respondent_emails.append(respondent.email)

        if respondent_emails:
            try:
                email_service = EmailService(db)
                success = email_service.notify_respondents_about_review_request(  # Сохраняем результат
                    goal_id=db_goal.id,  # type: ignore
                    employee_name=current_user.full_name,  # type: ignore
                    respondent_emails=respondent_emails,
                )
                if not success:
                    # Логируем ошибку, но НЕ прерываем выполнение
                    logger.info("Failed to send some email notifications")
            except Exception as e:
                # Ловим любые ошибки при отправке email, но НЕ падаем
                logger.info(f"Email notification error: {e}")
    return db_goal


@router.get(
    "/employee/{employee_id}",
    response_model=List[GoalResponse],
    summary="Цели сотрудника",
    description="Получение списка целей сотрудника. Доступно самому сотруднику или его руководителю.",
)
async def get_employee_goals(
    employee_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение целей сотрудника"""
    # Проверяем что пользователь запрашивает свои цели или является руководителем
    if employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view these goals"
        )

    goals = db.query(GoalModel).filter(GoalModel.employee_id == employee_id).all()

    # Добавляем имя сотрудника к ответу
    for goal in goals:
        goal.employee_name = goal.employee.full_name  # type: ignore

    return goals


@router.get(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Получение цели",
    description="Получение конкретной цели по ID. Проверяются права доступа.",
)
async def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение конкретной цели"""
    goal = db.query(GoalModel).filter(GoalModel.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем права доступа
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized to view this goal")

    goal.employee_name = goal.employee.full_name  # type: ignore
    return goal
