from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.database.session import get_db
from app.models.schemas import (
    ReviewCreate,
    ReviewResponse,
    ReviewResponseWithAnswers,
    RespondentReviewCreate,
    FinalReviewUpdate,
    ReviewType,
)
from app.models.database import Review, RespondentReview, Goal, User, QuestionTemplate
from app.api.endpoints.auth import get_current_user
from app.services.review_service import ReviewService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService

router = APIRouter(tags=["reviews"])


@router.post(
    "/",
    response_model=ReviewResponse,
    summary="Создание оценки",
    description="""
    Создание оценки разных типов:
    
    - **self**: Самооценка (только владелец цели)
    - **manager**: Оценка руководителя (только руководители)  
    - **potential**: Оценка потенциала
    - **respondent**: Оценка респондента
    
    Автоматически рассчитывает баллы и отправляет уведомления.
    """,
)
async def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создание оценки (самооценка, оценка руководителя, оценка потенциала)"""
    # Проверяем существование цели
    goal = db.query(Goal).filter(Goal.id == review.goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем права доступа
    if review.review_type == ReviewType.SELF:
        # Самооценка - только владелец цели
        if goal.employee_id != current_user.id:  # type: ignore
            raise HTTPException(
                status_code=403, detail="Can only create self-review for your own goals"
            )
    elif review.review_type == ReviewType.MANAGER:
        # Оценка руководителя - только руководители
        if not current_user.is_manager:  # type: ignore
            raise HTTPException(
                status_code=403, detail="Only managers can create manager reviews"
            )

    # Проверяем, не существует ли уже ревью такого типа
    existing_review = (
        db.query(Review)
        .filter(
            Review.goal_id == review.goal_id,
            Review.reviewer_id == current_user.id,
            Review.review_type == review.review_type,
        )
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=400, detail="Review of this type already exists"
        )

    # Рассчитываем баллы
    review_service = ReviewService(db)
    score = review_service.calculate_review_score(review.answers, review.review_type)

    # Сохраняем ревью
    db_review = Review(
        goal_id=review.goal_id,
        reviewer_id=current_user.id,
        review_type=review.review_type,
        calculated_score=score,
    )

    # Сохраняем ответы в соответствующие поля
    answers_json = json.dumps([answer.model_dump() for answer in review.answers])

    if review.review_type == ReviewType.SELF:
        db_review.self_evaluation_answers = answers_json  # type: ignore
    elif review.review_type == ReviewType.MANAGER:
        db_review.manager_evaluation_answers = answers_json  # type: ignore
    elif review.review_type == ReviewType.POTENTIAL:
        db_review.potential_evaluation_answers = answers_json  # type: ignore

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # АВТОМАТИЧЕСКОЕ УВЕДОМЛЕНИЕ РУКОВОДИТЕЛЯ ПРИ САМООЦЕНКЕ
    if review.review_type == ReviewType.SELF:
        goal = db.query(Goal).filter(Goal.id == review.goal_id).first()
        if goal:
            user_service = UserService(db)
            manager = user_service.get_user_manager(
                goal.employee_id  # type: ignore
            )  # Руководитель владельца цели

            # Если у сотрудника нет назначенного руководителя, берем любого менеджера
            if not manager:
                managers = user_service.get_all_managers()
                manager = managers[0] if managers else None

            if manager and manager.email:  # type: ignore
                email_service = EmailService(db)
                email_service.notify_manager_about_pending_review(
                    goal_id=goal.id,  # type: ignore
                    employee_name=current_user.full_name,  # type: ignore
                    manager_email=manager.email,  # type: ignore
                )

            # СОЗДАЕМ IN-APP УВЕДОМЛЕНИЕ
            if manager:
                notification_service = NotificationService(db)
                notification_service.create_review_pending_notification(
                    goal_id=goal.id,  # type: ignore
                    employee_name=current_user.full_name,  # type: ignore
                    manager_id=manager.id,  # type: ignore
                )
    return ReviewResponse(
        id=db_review.id,  # type: ignore
        goal_id=db_review.goal_id,  # type: ignore
        reviewer_id=db_review.reviewer_id,  # type: ignore
        review_type=db_review.review_type,  # type: ignore
        calculated_score=db_review.calculated_score,  # type: ignore
        created_at=db_review.created_at,  # type: ignore
        final_rating=db_review.final_rating,  # type: ignore
        final_feedback=db_review.final_feedback,  # type: ignore
    )


@router.get(
    "/{review_id}",
    response_model=ReviewResponseWithAnswers,
    summary="Получение оценки с ответами",
    description="Получение полной информации об оценке включая все ответы на вопросы.",
)
async def get_review_with_answers(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение ревью с ответами"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Проверяем права доступа
    goal = review.goal
    if goal.employee_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view this review"
        )

    # Создаем ответ с парсингом JSON
    result = ReviewResponseWithAnswers(
        id=review.id,  # type: ignore
        goal_id=review.goal_id,  # type: ignore
        reviewer_id=review.reviewer_id,  # type: ignore
        review_type=review.review_type,  # type: ignore
        calculated_score=review.calculated_score,  # type: ignore
        created_at=review.created_at,  # type: ignore
        final_rating=review.final_rating,  # type: ignore
        final_feedback=review.final_feedback,  # type: ignore
    )

    # Парсим JSON ответы
    if review.self_evaluation_answers:  # type: ignore
        result.self_evaluation_answers = json.loads(review.self_evaluation_answers)  # type: ignore
    if review.manager_evaluation_answers:  # type: ignore
        result.manager_evaluation_answers = json.loads(
            review.manager_evaluation_answers  # type: ignore
        )
    if review.potential_evaluation_answers:  # type: ignore
        result.potential_evaluation_answers = json.loads(
            review.potential_evaluation_answers  # type: ignore
        )

    return result


@router.put(
    "/{review_id}/final",
    response_model=ReviewResponse,
    summary="Завершение оценки",
    description="Завершение оценки руководителем - проставление итогового рейтинга и обратной связи. Доступно только руководителям.",
)
async def update_final_review(
    review_id: str,
    final_data: FinalReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Завершение ревью руководителем - проставление рейтинга и обратной связи"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Only managers can finalize reviews"
        )

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.final_rating = final_data.final_rating  # type: ignore
    review.final_feedback = final_data.final_feedback  # type: ignore

    db.commit()
    db.refresh(review)

    # АВТОМАТИЧЕСКОЕ УВЕДОМЛЕНИЕ СОТРУДНИКА О ЗАВЕРШЕНИИ РЕВЬЮ
    goal = review.goal
    employee = goal.employee

    if employee and employee.email:
        email_service = EmailService(db)
        email_service.notify_employee_about_final_review(
            goal_id=goal.id,
            employee_email=employee.email,
            manager_name=current_user.full_name,  # type: ignore
            final_rating=final_data.final_rating,
        )

    # IN-APP УВЕДОМЛЕНИЕ ДЛЯ СОТРУДНИКА
    if employee:
        notification_service = NotificationService(db)
        notification_service.create_review_completed_notification(
            goal_id=goal.id,
            manager_name=current_user.full_name,  # type: ignore
            employee_id=employee.id,
        )

    return ReviewResponse(
        id=review.id,  # type: ignore
        goal_id=review.goal_id,  # type: ignore
        reviewer_id=review.reviewer_id,  # type: ignore
        review_type=review.review_type,  # type: ignore
        calculated_score=review.calculated_score,  # type: ignore
        created_at=review.created_at,  # type: ignore
        final_rating=review.final_rating,  # type: ignore
        final_feedback=review.final_feedback,  # type: ignore
    )
