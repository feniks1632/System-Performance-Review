from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.database import Goal, GoalStep, User
from app.api.endpoints.auth import get_current_user
from app.models.schemas import (
    GoalStepResponse,
    GoalStepCreate,
    GoalStepUpdate,
    SuccessResponse
)

router = APIRouter(tags=["goal-steps"])


@router.post(
    "/goals/{goal_id}/steps",
    response_model=GoalStepResponse,
    summary="Добавление подпункта к цели",
    description="Добавление нового подпункта/шага для достижения цели. Максимум 3 подпункта на цель.",
)
async def create_goal_step(
    goal_id: str,
    step_data: GoalStepCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Добавление подпункта к цели"""
    # Проверяем существование цели
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем права доступа
    if goal.employee_id != current_user.id:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Can only add steps to your own goals"
        )

    # Проверяем лимит подпунктов (максимум 3)
    existing_steps_count = db.query(GoalStep).filter(GoalStep.goal_id == goal_id).count()
    if existing_steps_count >= 3:
        raise HTTPException(
            status_code=400, detail="Maximum 3 steps allowed per goal"
        )

    # Создаем подпункт
    step = GoalStep(
        goal_id=goal_id,
        title=step_data.title,
        description=step_data.description,
        order_index=step_data.order_index or existing_steps_count
    )

    db.add(step)
    db.commit()
    db.refresh(step)

    return step


@router.get(
    "/goals/{goal_id}/steps",
    response_model=List[GoalStepResponse],
    summary="Получение подпунктов цели",
    description="Получение всех подпунктов/шагов для конкретной цели.",
)
async def get_goal_steps(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение подпунктов цели"""
    # Проверяем существование цели
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем права доступа
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view these goal steps"
        )

    steps = db.query(GoalStep).filter(GoalStep.goal_id == goal_id).order_by(GoalStep.order_index).all()
    return steps


@router.put(
    "/steps/{step_id}",
    response_model=GoalStepResponse,
    summary="Обновление подпункта",
    description="Обновление подпункта цели (название, описание, статус выполнения).",
)
async def update_goal_step(
    step_id: str,
    step_data: GoalStepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление подпункта цели"""
    step = db.query(GoalStep).filter(GoalStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Goal step not found")

    # Проверяем права доступа через цель
    goal = step.goal
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to update this goal step"
        )

    # Обновляем поля
    if step_data.title is not None:
        step.title = step_data.title  # type: ignore
    
    if step_data.description is not None:
        step.description = step_data.description  # type: ignore
    
    if step_data.is_completed is not None:
        step.is_completed = step_data.is_completed  # type: ignore
    
    if step_data.order_index is not None:
        step.order_index = step_data.order_index  # type: ignore

    db.commit()
    db.refresh(step)

    return step


@router.delete(
    "/steps/{step_id}",
    response_model=SuccessResponse,
    summary="Удаление подпункта",
    description="Удаление подпункта цели.",
)
async def delete_goal_step(
    step_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удаление подпункта цели"""
    step = db.query(GoalStep).filter(GoalStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Goal step not found")

    # Проверяем права доступа через цель
    goal = step.goal
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this goal step"
        )

    db.delete(step)
    db.commit()

    return SuccessResponse(message="Goal step deleted successfully")


@router.put(
    "/steps/{step_id}/complete",
    response_model=GoalStepResponse,
    summary="Отметить подпункт как выполненный",
    description="Отметка подпункта как выполненного.",
)
async def complete_goal_step(
    step_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отметить подпункт как выполненный"""
    step = db.query(GoalStep).filter(GoalStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Goal step not found")

    # Проверяем права доступа через цель
    goal = step.goal
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to update this goal step"
        )

    step.is_completed = True  # type: ignore
    db.commit()
    db.refresh(step)

    return step


@router.put(
    "/steps/{step_id}/incomplete", 
    response_model=GoalStepResponse,
    summary="Отметить подпункт как невыполненный",
    description="Отметка подпункта как невыполненного.",
)
async def incomplete_goal_step(
    step_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отметить подпункт как невыполненный"""
    step = db.query(GoalStep).filter(GoalStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Goal step not found")

    # Проверяем права доступа через цель
    goal = step.goal
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to update this goal step"
        )

    step.is_completed = False  # type: ignore
    db.commit()
    db.refresh(step)

    return step