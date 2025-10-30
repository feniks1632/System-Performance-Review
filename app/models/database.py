from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    ForeignKey,
    Float,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid


class Base(DeclarativeBase):
    pass


def generate_uuid():
    return str(uuid.uuid4())


# Связь многие-ко-многим для респондентов
goal_respondents = Table(
    "goal_respondents",
    Base.metadata,
    Column("goal_id", String, ForeignKey("goals.id")),
    Column("user_id", String, ForeignKey("users.id")),
)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_manager = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # СВЯЗЬ С РУКОВОДИТЕЛЕМ
    manager_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    goals = relationship(
        "Goal", back_populates="employee", foreign_keys="Goal.employee_id"
    )
    reviews_created = relationship(
        "Review", back_populates="reviewer", foreign_keys="Review.reviewer_id"
    )
    respondent_reviews = relationship("RespondentReview", back_populates="respondent")

    # ОБРАТНЫЕ СВЯЗИ ДЛЯ РУКОВОДИТЕЛЯ
    manager = relationship("User", remote_side=[id], backref="subordinates")


class GoalStep(Base):
    """Подпункты/шаги для достижения цели"""

    __tablename__ = "goal_steps"

    id = Column(String, primary_key=True, default=generate_uuid)
    goal_id = Column(String, ForeignKey("goals.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)  # для порядка следования
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    goal = relationship("Goal", back_populates="steps")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=generate_uuid)
    employee_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    expected_result = Column(Text)
    deadline = Column(DateTime)
    task_link = Column(String)  # Опционально
    status = Column(String, default="active")  # active, completed, cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    employee = relationship("User", back_populates="goals", foreign_keys=[employee_id])
    respondents = relationship("User", secondary=goal_respondents)
    reviews = relationship("Review", back_populates="goal")
    respondent_reviews = relationship("RespondentReview", back_populates="goal")
    steps = relationship(
        "GoalStep", back_populates="goal", cascade="all, delete-orphan"
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=generate_uuid)
    goal_id = Column(String, ForeignKey("goals.id"), nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    review_type = Column(String, nullable=False)  # 'self', 'manager', 'potential'

    # Этап 1: Самооценка
    self_evaluation_answers = Column(Text)  # JSON

    # Этап 2: Оценка руководителя
    manager_evaluation_answers = Column(Text)  # JSON
    manager_feedback = Column(Text)

    # Этап 3: Оценка потенциала
    potential_evaluation_answers = Column(Text)  # JSON

    # Итоговые результаты
    final_rating = Column(String)  # A, B, C, D
    final_feedback = Column(Text)
    calculated_score = Column(Float)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    goal = relationship("Goal", back_populates="reviews")
    reviewer = relationship(
        "User", back_populates="reviews_created", foreign_keys=[reviewer_id]
    )


class RespondentReview(Base):
    __tablename__ = "respondent_reviews"

    id = Column(String, primary_key=True, default=generate_uuid)
    goal_id = Column(String, ForeignKey("goals.id"), nullable=False)
    respondent_id = Column(String, ForeignKey("users.id"), nullable=False)
    answers = Column(Text)  # JSON
    comments = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    goal = relationship("Goal", back_populates="respondent_reviews")
    respondent = relationship("User", back_populates="respondent_reviews")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        String, nullable=False
    )  # 'review_pending', 'review_completed', 'goal_created'
    related_entity_type = Column(String)  # 'review', 'goal', 'user'
    related_entity_id = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="notifications")


class QuestionTemplate(Base):
    __tablename__ = "question_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    question_text = Column(Text, nullable=False)
    question_type = Column(
        String, nullable=False
    )  # 'self', 'manager', 'potential', 'respondent'
    section = Column(
        String
    )  # Для потенциала: 'professional', 'personal', 'development'
    weight = Column(Float, default=1.0)
    max_score = Column(Integer, default=5)
    order_index = Column(Integer, default=0)
    trigger_words = Column(Text)  # JSON с триггерными словами для рекомендаций
    options_json = Column(Text)  # JSON с вариантами ответов
    requires_manager_scoring = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
