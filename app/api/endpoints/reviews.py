from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
import json

from app.api.endpoints.auth import get_current_user
from app.core.logger import logger
from app.database.session import get_db
from app.models.schemas import (
    Answer,
    ReviewCreate,
    ReviewResponse,
    ReviewResponseWithAnswers,
    RespondentReviewCreate,
    FinalReviewUpdate,
    ReviewType,
    RespondentReviewResponse,
    SuccessResponse,
)
from app.models.database import Review, RespondentReview, Goal, User
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
    Создание оценки разных типов с новой системой подсчета баллов:
    
    - **self**: Самооценка (только владелец цели)
    - **manager**: Оценка руководителя (только руководители)  
    - **potential**: Оценка потенциала
    - **respondent**: Оценка респондента
    
    Автоматически рассчитывает баллы с учетом весов вопросов и отправляет уведомления.
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

    # РАСЧЕТ БАЛЛОВ
    review_service = ReviewService(db)

    if review.review_type == ReviewType.POTENTIAL:
        # Для оценки потенциала
        potential_scores = review_service.calculate_potential_score(review.answers)
        score = potential_scores["total_potential_score"]

        # Сохраняем детальные баллы потенциала в JSON
        potential_details = json.dumps(potential_scores)
    else:
        # Для других типов используем стандартный расчет
        score = review_service.calculate_weighted_score(
            review.answers, review.review_type
        )
        potential_details = None

    # ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ НА ОСНОВЕ ТРИГГЕРНЫХ СЛОВ
    recommendations = review_service.extract_trigger_words_feedback(review.answers)

    # Сохраняем ревью
    db_review = Review(
        goal_id=review.goal_id,
        reviewer_id=current_user.id,
        review_type=review.review_type,
        calculated_score=score,
        final_feedback=(
            json.dumps(recommendations) if recommendations else None
        ),  # Сохраняем рекомендации
    )

    # Сохраняем ответы в соответствующие поля
    answers_json = json.dumps([answer.model_dump() for answer in review.answers])

    if review.review_type == ReviewType.SELF:
        db_review.self_evaluation_answers = answers_json  # type: ignore
    elif review.review_type == ReviewType.MANAGER:
        db_review.manager_evaluation_answers = answers_json  # type: ignore
    elif review.review_type == ReviewType.POTENTIAL:
        db_review.potential_evaluation_answers = answers_json  # type: ignore
        # Сохраняем детали потенциала
        db_review.manager_feedback = potential_details  # type: ignore

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # АВТОМАТИЧЕСКОЕ УВЕДОМЛЕНИЕ РУКОВОДИТЕЛЯ ПРИ САМООЦЕНКЕ
    if review.review_type == ReviewType.SELF:
        user_service = UserService(db)
        manager = user_service.get_user_manager(goal.employee_id)  # type: ignore

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


@router.post(
    "/respondent",
    response_model=RespondentReviewResponse,
    summary="Создание оценки респондента",
    description="""
    Создание оценки респондентом с новой системой подсчета баллов.
    
    - **Только назначенные респонденты** могут оценивать цель
    - **Автоматический расчет баллов** на основе ответов с учетом весов
    - **Генерация рекомендаций** на основе триггерных слов
    """,
)
async def create_respondent_review(
    review: RespondentReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создание оценки респондента"""
    # Проверяем существование цели
    goal = db.query(Goal).filter(Goal.id == review.goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Проверяем что пользователь является респондентом цели
    if current_user not in goal.respondents:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized as respondent for this goal"
        )

    # Проверяем, не существует ли уже оценка от этого респондента
    existing_review = (
        db.query(RespondentReview)
        .filter(
            RespondentReview.goal_id == review.goal_id,
            RespondentReview.respondent_id == current_user.id,
        )
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=400, detail="Respondent review already exists for this goal"
        )

    # РАСЧЕТ БАЛЛОВ
    review_service = ReviewService(db)
    score = review_service.calculate_weighted_score(
        review.answers, ReviewType.RESPONDENT
    )

    # ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ
    recommendations = review_service.extract_trigger_words_feedback(review.answers)

    # Формируем комментарии с рекомендациями
    enhanced_comments = review.comments
    if recommendations:
        recommendations_text = "Рекомендации системы:\n" + "\n".join(recommendations)
        if enhanced_comments:
            enhanced_comments += "\n\n" + recommendations_text
        else:
            enhanced_comments = recommendations_text

    # Сохраняем оценку респондента
    db_review = RespondentReview(
        goal_id=review.goal_id,
        respondent_id=current_user.id,
        answers=json.dumps([answer.model_dump() for answer in review.answers]),
        comments=enhanced_comments,  # type: ignore
    )

    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Добавляем имя респондента для ответа
    db_review.respondent_name = current_user.full_name  # type: ignore

    return RespondentReviewResponse(
        id=db_review.id,  # type: ignore
        goal_id=db_review.goal_id,  # type: ignore
        respondent_id=db_review.respondent_id,  # type: ignore
        answers=review.answers,
        comments=db_review.comments,  # type: ignore
        created_at=db_review.created_at,  # type: ignore
        respondent_name=current_user.full_name,  # type: ignore
    )


@router.get(
    "/respondent/{review_id}",
    response_model=RespondentReviewResponse,
    summary="Получение оценки респондента",
    description="Получение конкретной оценки респондента по ID.",
)
async def get_respondent_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение оценки респондента"""
    review = db.query(RespondentReview).filter(RespondentReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Respondent review not found")

    # Проверяем права доступа
    goal = review.goal
    if (
        goal.employee_id != current_user.id
        and not current_user.is_manager  # type: ignore
        and review.respondent_id != current_user.id
    ):  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view this respondent review"
        )

    # Парсим JSON ответы и преобразуем в List[Answer]
    parsed_answers = []
    if review.answers:  # type: ignore
        try:
            answers_data = json.loads(review.answers)  # type: ignore
            parsed_answers = [Answer(**answer_data) for answer_data in answers_data]
        except Exception as e:
            logger.error(f"Error parsing answers for review {review.id}: {e}")
            parsed_answers = []

    return RespondentReviewResponse(
        id=review.id,  # type: ignore
        goal_id=review.goal_id,  # type: ignore
        respondent_id=review.respondent_id,  # type: ignore
        answers=parsed_answers,  # Теперь это List[Answer]
        comments=review.comments,  # type: ignore
        created_at=review.created_at,  # type: ignore
        respondent_name=review.respondent.full_name,  # type: ignore
    )


@router.post(
    "/{review_id}/score-manager-questions",
    response_model=SuccessResponse,
    summary="Оценка вопросов руководителем",
)
async def score_manager_questions(
    review_id: str,
    scores: List[Answer],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Руководитель оценивает вопросы по 10-балльной системе"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(status_code=403, detail="Only managers can score questions")

    review_service = ReviewService(db)
    review = db.query(Review).filter(Review.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Валидация оценок (1-10)
    for score_data in scores:
        if score_data.score is not None and (
            score_data.score < 1 or score_data.score > 10
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Score must be between 1 and 10 for question {score_data.question_id}",
            )

    # Обновляем оценки в соответствующих полях
    if review.review_type == ReviewType.SELF and review.self_evaluation_answers:  # type: ignore
        answers_data = json.loads(review.self_evaluation_answers)  # type: ignore
        for score_data in scores:
            for answer in answers_data:
                if answer.get("question_id") == score_data.question_id:
                    answer["score"] = score_data.score
        review.self_evaluation_answers = json.dumps(answers_data)  # type: ignore

    elif review.review_type == ReviewType.RESPONDENT and hasattr(review, "answers"):  # type: ignore
        answers_data = json.loads(review.answers)  # type: ignore
        for score_data in scores:
            for answer in answers_data:
                if answer.get("question_id") == score_data.question_id:
                    answer["score"] = score_data.score  # type: ignore
        review.answers = json.dumps(answers_data)  # type: ignore

    # Пересчитываем общий балл
    updated_answers = [Answer(**data) for data in answers_data]  # type: ignore
    total_score = review_service.calculate_weighted_score(updated_answers, review.review_type)  # type: ignore
    review.calculated_score = total_score  # type: ignore

    db.commit()

    return SuccessResponse(
        message=f"Questions scored successfully. New total score: {total_score:.2f}"
    )


@router.get(
    "/{review_id}/pending-manager-scores",
    response_model=List[Dict],
    summary="Получить вопросы, ожидающие оценку руководителя",
)
async def get_pending_manager_scores(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список вопросов, которые нужно оценить руководителю"""
    review_service = ReviewService(db)
    return review_service.get_pending_manager_scoring_questions(review_id)
