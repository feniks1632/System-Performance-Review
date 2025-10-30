from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.database import QuestionTemplate, User
from app.api.endpoints.auth import get_current_user
from app.models.schemas import (
    QuestionTemplateCreate,
    QuestionTemplateResponse,
    SuccessResponse,
)

router = APIRouter(tags=["question-templates"])


@router.post(
    "/",
    response_model=QuestionTemplateResponse,
    summary="Создание шаблона вопроса",
    description="Создание нового шаблона вопроса для системы оценки. Только для руководителей.",
)
async def create_question_template(
    template_data: QuestionTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создание шаблона вопроса"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Only managers can create question templates"
        )

    # Создаем шаблон
    template = QuestionTemplate(
        question_text=template_data.question_text,
        question_type=template_data.question_type,
        section=template_data.section,
        weight=template_data.weight,
        max_score=template_data.max_score,
        order_index=template_data.order_index,
        trigger_words=template_data.trigger_words,
        requires_manager_scoring=template_data.requires_manager_scoring,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get(
    "/",
    response_model=List[QuestionTemplateResponse],
    summary="Получение списка шаблонов вопросов",
    description="Получение всех активных шаблонов вопросов с фильтрацией по типу.",
)
async def get_question_templates(
    question_type: Optional[str] = Query(None, description="Фильтр по типу вопроса"),
    section: Optional[str] = Query(None, description="Фильтр по разделу"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение списка шаблонов вопросов"""
    query = db.query(QuestionTemplate).filter(QuestionTemplate.is_active == True)

    if question_type:
        query = query.filter(QuestionTemplate.question_type == question_type)

    if section:
        query = query.filter(QuestionTemplate.section == section)

    templates = query.order_by(QuestionTemplate.order_index).all()
    return templates


@router.get(
    "/{template_id}",
    response_model=QuestionTemplateResponse,
    summary="Получение шаблона вопроса по ID",
    description="Получение конкретного шаблона вопроса по его идентификатору.",
)
async def get_question_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получение шаблона вопроса по ID"""
    template = (
        db.query(QuestionTemplate).filter(QuestionTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Question template not found")

    return template


@router.put(
    "/{template_id}",
    response_model=QuestionTemplateResponse,
    summary="Обновление шаблона вопроса",
    description="Обновление шаблона вопроса. Только для руководителей.",
)
async def update_question_template(
    template_id: str,
    template_data: QuestionTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновление шаблона вопроса"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Only managers can update question templates"
        )

    template = (
        db.query(QuestionTemplate).filter(QuestionTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Question template not found")

    # Обновляем поля
    template.question_text = template_data.question_text  # type: ignore
    template.question_type = template_data.question_type  # type: ignore
    template.section = template_data.section  # type: ignore
    template.weight = template_data.weight  # type: ignore
    template.max_score = template_data.max_score  # type: ignore
    template.order_index = template_data.order_index  # type: ignore
    template.trigger_words = template_data.trigger_words  # type: ignore
    template.requires_manager_scoring = template_data.requires_manager_scoring  # type: ignore

    db.commit()
    db.refresh(template)

    return template


@router.delete(
    "/{template_id}",
    response_model=SuccessResponse,
    summary="Удаление шаблона вопроса",
    description="Мягкое удаление шаблона вопроса (is_active=False). Только для руководителей.",
)
async def delete_question_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удаление шаблона вопроса"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Only managers can delete question templates"
        )

    template = (
        db.query(QuestionTemplate).filter(QuestionTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Question template not found")

    template.is_active = False  # type: ignore
    db.commit()

    return SuccessResponse(message="Question template deleted successfully")
