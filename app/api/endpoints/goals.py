from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.endpoints.auth import get_current_user
from app.core.logger import logger
from app.database.session import get_db
from app.models.schemas import GoalCreate, GoalResponse, SuccessResponse
from app.models.database import Goal as GoalModel, GoalStep, User
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService


router = APIRouter(tags=["goals"])


@router.post(
    "/",
    response_model=GoalResponse,
    summary="Создание цели",
    description="""
    Создание новой цели для сотрудника.
    
    - **Максимум 5 целей на сотрудника**
    - **Максимум 3 подпункта на цель**
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

    # Проверяем количество подпунктов (максимум 3)
    if goal.steps and len(goal.steps) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 steps allowed per goal")

    if goal.respondent_ids and len(goal.respondent_ids) > 5:
        raise HTTPException(
            status_code=400, detail="Maximum 5 respondents allowed per goal"
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

    # Добавляем подпункты если есть
    if goal.steps:
        for i, step_data in enumerate(goal.steps):
            step = GoalStep(
                goal_id=db_goal.id,  # type: ignore
                title=step_data.title,
                description=step_data.description,
                order_index=step_data.order_index or i,
            )
            db.add(step)
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
                success = email_service.notify_respondents_about_review_request(
                    goal_id=db_goal.id,  # type: ignore
                    employee_name=current_user.full_name,  # type: ignore
                    respondent_emails=respondent_emails,
                )
                if not success:
                    logger.info("Failed to send some email notifications")
            except Exception as e:
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

    # Добавляем имя сотрудника и подпункты к ответу
    for goal in goals:
        goal.employee_name = goal.employee.full_name  # type: ignore
        # Подпункты автоматически загрузятся через relationship

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

    # РАСШИРЕННАЯ ПРОВЕРКА ПРАВ ДОСТУПА - ПРОВЕРКА НА РЕСПОНДЕНТА
    is_owner = goal.employee_id == current_user.id
    is_manager = current_user.is_manager
    is_respondent = any(
        respondent.id == current_user.id for respondent in goal.respondents
    )

    if not (is_owner or is_manager or is_respondent):  # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized to view this goal")

    goal.employee_name = goal.employee.full_name  # type: ignore
    return goal


@router.put(
    "/{goal_id}/status",
    response_model=SuccessResponse,
    summary="Обновление статуса цели",
    description="Обновление статуса цели (active, completed, cancelled).",
)
async def update_goal_status(
    goal_id: str,
    status_data: dict,  # Принимаем JSON объект
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление статуса цели"""
    goal = db.query(GoalModel).filter(GoalModel.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверка прав
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized")

    # Извлекаем статус из JSON объекта
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=422, detail="Status field is required")

    # Проверяем что статус валидный
    valid_statuses = ["active", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=422, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    goal.status = new_status  # type: ignore
    db.commit()

    return SuccessResponse(message=f"Goal status updated to {new_status}")


@router.get(
    "/respondent/my",
    response_model=List[GoalResponse],
    summary="Цели, где я являюсь респондентом",
    description="Получение списка целей, где текущий пользователь назначен респондентом.",
)
async def get_my_respondent_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение целей, где пользователь является респондентом"""
    goals = (
        db.query(GoalModel)
        .join(GoalModel.respondents)
        .filter(User.id == current_user.id)
        .all()
    )

    for goal in goals:
        goal.employee_name = goal.employee.full_name  # type: ignore

    return goals


@router.get(
    "/respondent/{goal_id}",
    response_model=GoalResponse,
    summary="Получение цели для респондента",
    description="Получение конкретной цели по ID, если пользователь является респондентом этой цели.",
)
async def get_goal_as_respondent(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение цели респондентом"""
    goal = db.query(GoalModel).filter(GoalModel.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем, является ли пользователь респондентом этой цели
    is_respondent = any(
        respondent.id == current_user.id for respondent in goal.respondents
    )
    if not is_respondent:
        raise HTTPException(
            status_code=403, detail="Not authorized as respondent for this goal"
        )

    goal.employee_name = goal.employee.full_name  # type: ignore
    goal.respondent_names = [respondent.full_name for respondent in goal.respondents]  # type: ignore
    return goal
