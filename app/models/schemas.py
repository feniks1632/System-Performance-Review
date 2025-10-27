from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReviewType(str, Enum):
    """Типы оценки"""

    SELF = "self"
    MANAGER = "manager"
    POTENTIAL = "potential"
    RESPONDENT = "respondent"


class GoalStatus(str, Enum):
    """Статусы целей"""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FinalRating(str, Enum):
    """Итоговые рейтинги"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


# === СХЕМЫ АУТЕНТИФИКАЦИИ ===
class UserBase(BaseModel):
    """Базовая схема пользователя"""

    email: EmailStr
    full_name: str
    is_manager: bool = False


class UserCreate(UserBase):
    """Создание пользователя"""

    password: str
    manager_id: Optional[str] = None  # ДОБАВЛЯЕМ ВЫБОР РУКОВОДИТЕЛЯ

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class UserLogin(BaseModel):
    """Вход в систему"""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Ответ с данными пользователя"""

    id: str
    is_active: bool
    created_at: datetime
    manager_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT токен"""

    access_token: str
    token_type: str
    user: UserResponse


# === СХЕМЫ ЦЕЛЕЙ ===
class GoalBase(BaseModel):
    """Базовая схема цели"""

    title: str
    description: str
    expected_result: str
    deadline: datetime
    task_link: Optional[str] = None


class GoalCreate(GoalBase):
    """Создание цели"""

    respondent_ids: Optional[List[str]] = []


class GoalResponse(GoalBase):
    """Ответ с данными цели"""

    id: str
    employee_id: str
    status: str = "active"
    created_at: datetime
    employee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# === СХЕМЫ ОЦЕНОК ===
class Answer(BaseModel):
    """Ответ на вопрос в оценке"""

    question_id: str
    answer: str
    score: Optional[float] = None


class ReviewCreate(BaseModel):
    """Создание оценки"""

    goal_id: str
    review_type: ReviewType
    answers: List[Answer]


class ReviewResponseBase(BaseModel):
    """Базовая схема ответа оценки"""

    id: str
    goal_id: str
    reviewer_id: str
    review_type: ReviewType
    calculated_score: Optional[float] = None
    created_at: datetime
    final_rating: Optional[str] = None
    final_feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewResponseWithAnswers(ReviewResponseBase):
    """Полная схема оценки с ответами"""

    self_evaluation_answers: Optional[List[Dict[str, Any]]] = None
    manager_evaluation_answers: Optional[List[Dict[str, Any]]] = None
    potential_evaluation_answers: Optional[List[Dict[str, Any]]] = None


# Алиас для простоты
ReviewResponse = ReviewResponseBase


class RespondentReviewCreate(BaseModel):
    """Создание оценки респондента"""

    goal_id: str
    answers: List[Answer]
    comments: Optional[str] = None


class FinalReviewUpdate(BaseModel):
    """Завершение оценки руководителем"""

    final_rating: str
    final_feedback: str


# === СХЕМЫ АНАЛИТИКИ ===
class GoalScores(BaseModel):
    """Баллы по цели"""

    self_score: float
    manager_score: float
    respondent_score: float
    total_score: float


class GoalAnalyticsResponse(BaseModel):
    """Аналитика по цели"""

    goal_id: str
    goal_title: str
    scores: GoalScores
    final_rating: str
    recommendations: List[str]
    review_count: int
    respondent_count: int


class EmployeeSummaryResponse(BaseModel):
    """Сводная аналитика по сотруднику"""

    employee_id: str
    total_goals: int
    completed_goals: int
    average_score: float
    overall_rating: str
    goals_analytics: List[GoalAnalyticsResponse]


# === СХЕМЫ УВЕДОМЛЕНИЙ ===
class NotificationResponse(BaseModel):
    """Уведомление"""

    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    """Количество непрочитанных уведомлений"""

    unread_count: int


# === СХЕМЫ ШАБЛОНОВ ВОПРОСОВ ===
class QuestionTemplateResponse(BaseModel):
    """Шаблон вопроса"""

    id: str
    question_type: str
    question_text: str
    possible_answers: Optional[Dict[str, Any]] = None
    weight: float = 1.0
    trigger_words: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === ОБЩИЕ СХЕМЫ ===
class SuccessResponse(BaseModel):
    """Успешный ответ"""

    status: str = "success"
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Ошибка"""

    detail: str


class ValidationErrorResponse(BaseModel):
    """Ошибка валидации"""

    detail: List[Dict[str, Any]]
