from typing import List, Dict, Any
import json
from sqlalchemy.orm import Session
from app.models.schemas import Answer
from app.models.database import QuestionTemplate


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_review_score(self, answers: List[Answer], review_type: str) -> float:
        """Расчет баллов за ответы с учетом весов вопросов"""
        total_score = 0.0
        total_weight = 0.0

        for answer in answers:
            question = (
                self.db.query(QuestionTemplate)
                .filter(QuestionTemplate.id == answer.question_id)
                .first()
            )

            if question and answer.score is not None:
                weight = question.weight if question.weight else 1.0  # type: ignore
                total_score += answer.score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0  # type: ignore

    def calculate_final_rating(self, total_score: float) -> str:
        """Определение рейтинга на основе итогового балла"""
        if total_score >= 4.5:
            return "A"
        elif total_score >= 4.0:
            return "B"
        elif total_score >= 3.0:
            return "C"
        else:
            return "D"
