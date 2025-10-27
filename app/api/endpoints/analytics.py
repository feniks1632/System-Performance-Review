from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.database import User
from app.api.endpoints.auth import get_current_user
from app.services.analytics_service import AnalyticsService
from app.models.schemas import GoalAnalyticsResponse, EmployeeSummaryResponse

router = APIRouter(tags=["analytics"])


@router.get(
    "/goal/{goal_id}",
    response_model=GoalAnalyticsResponse,
    summary="Аналитика по цели",
    description="Детальная аналитика по конкретной цели включая баллы, рейтинги и рекомендации.",
)
async def get_goal_analytics(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Аналитика по конкретной цели"""
    analytics_service = AnalyticsService(db)
    analytics = analytics_service.get_goal_analytics(goal_id)

    if not analytics:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем права доступа
    from app.models.database import Goal

    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view this analytics"
        )

    return analytics


@router.get(
    "/employee/{employee_id}/summary",
    response_model=EmployeeSummaryResponse,
    summary="Сводная аналитика по сотруднику",
    description="Общая аналитика по всем целям сотрудника с средними баллами и рейтингами.",
)
async def get_employee_summary(
    employee_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Сводная аналитика по сотруднику"""
    # Проверяем права доступа
    if employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view this employee's analytics"
        )

    analytics_service = AnalyticsService(db)
    summary = analytics_service.get_employee_summary(employee_id)

    return summary
