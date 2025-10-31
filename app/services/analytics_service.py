import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.database import Review, RespondentReview, Goal
from app.models.schemas import Answer, ReviewType
from app.services.review_service import ReviewService


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_goal_analytics(self, goal_id: str) -> Dict[str, Any]:
        """Комплексная аналитика по цели"""

        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return {}

        # Собираем все оценки
        reviews = self.db.query(Review).filter(Review.goal_id == goal_id).all()
        respondent_reviews = (
            self.db.query(RespondentReview)
            .filter(RespondentReview.goal_id == goal_id)
            .all()
        )

        # Расчет средних баллов
        scores = self._calculate_scores(reviews, respondent_reviews)

        # Генерация рекомендаций
        recommendations = self._generate_recommendations(reviews, respondent_reviews)

        return {
            "goal_id": goal_id,
            "goal_title": goal.title,
            "scores": scores,
            "final_rating": self._calculate_final_rating(scores["total_score"]),
            "recommendations": recommendations,
            "review_count": len(reviews),
            "respondent_count": len(respondent_reviews),
        }

    def _calculate_scores(
        self, reviews: List, respondent_reviews: List
    ) -> Dict[str, float]:
        """Расчет различных баллов"""
        scores = {
            "self_score": 0,
            "manager_score": 0,
            "respondent_score": 0,
            "potential_score": 0,
            "total_score": 0,
        }

        # Считаем самооценки
        self_scores = []
        for review in reviews:
            if review.review_type == ReviewType.SELF and review.calculated_score:
                self_scores.append(review.calculated_score)

        if self_scores:
            scores["self_score"] = sum(self_scores) / len(self_scores)  # type: ignore

        # Считаем оценки руководителя
        manager_scores = []
        for review in reviews:
            if review.review_type == ReviewType.MANAGER and review.calculated_score:
                manager_scores.append(review.calculated_score)

        if manager_scores:
            scores["manager_score"] = sum(manager_scores) / len(manager_scores)  # type: ignore

        # Считаем оценки респондентов
        respondent_scores = []
        for resp_review in respondent_reviews:
            # Используем логику расчета из ответов
            if resp_review.answers:
                try:
                    answers_data = json.loads(resp_review.answers)
                    answers = [Answer(**answer_data) for answer_data in answers_data]

                    review_service = ReviewService(self.db)
                    score = review_service.calculate_weighted_score(
                        answers, ReviewType.RESPONDENT
                    )
                    respondent_scores.append(score)
                except Exception as e:
                    logger.error(f"Error calculating respondent score: {e}")
                    continue

        if respondent_scores:
            scores["respondent_score"] = sum(respondent_scores) / len(respondent_scores)  # type: ignore

        # Считаем оценку потенциала
        potential_scores = []
        for review in reviews:
            if review.review_type == ReviewType.POTENTIAL and review.calculated_score:
                potential_scores.append(review.calculated_score)

        if potential_scores:
            scores["potential_score"] = sum(potential_scores) / len(potential_scores)  # type: ignore

        # РАСЧЕТ ОБЩЕГО БАЛЛА
        total_scores = []
        weights = []

        if scores["self_score"] > 0:
            total_scores.append(scores["self_score"])
            weights.append(1.0)  # Самооценка

        if scores["manager_score"] > 0:
            total_scores.append(scores["manager_score"])
            weights.append(1.8)  # Оценка руководителя - повышенный вес

        if scores["respondent_score"] > 0:
            total_scores.append(scores["respondent_score"])
            weights.append(0.7)  # Оценки респондентов

        if scores["potential_score"] > 0:
            total_scores.append(scores["potential_score"])
            weights.append(1.2)  # Оценка потенциала

        if total_scores:
            weighted_sum = sum(
                score * weight for score, weight in zip(total_scores, weights)
            )
            total_weight = sum(weights)
            scores["total_score"] = weighted_sum / total_weight  # type: ignore
        else:
            scores["total_score"] = 0

        return scores  # type: ignore

    def _calculate_final_rating(self, score: float) -> str:
        """Расчет итогового рейтинга на основе балла (шкала 0-5)"""
        if score >= 4.5:
            return "A"
        elif score >= 4.0:
            return "B"
        elif score >= 3.0:
            return "C"
        else:
            return "D"

    def _generate_recommendations(
        self, reviews: List, respondent_reviews: List
    ) -> List[str]:
        """Генерация рекомендаций на основе ответов"""
        all_text = self._extract_feedback_text(reviews, respondent_reviews)

        recommendations = []

        # Простая логика рекомендаций на основе ключевых слов
        problem_words = ["сложно", "трудно", "проблем", "тяжело", "затруднен"]
        success_words = ["успех", "достиг", "результат", "отличн", "превосходн"]
        communication_words = ["коммуникац", "общен", "взаимодейств", "команд"]

        if any(word in all_text for word in problem_words):
            recommendations.append(
                "Рекомендуется тренировка навыков преодоления сложностей"
            )

        if any(word in all_text for word in success_words):
            recommendations.append("Развивать навыки управления успешными проектами")

        if any(word in all_text for word in communication_words):
            recommendations.append("Улучшить навыки коммуникации и работы в команде")

        # Если нет специфических рекомендаций, даем общую
        if not recommendations:
            recommendations.append(
                "Рекомендуется индивидуальная консультация с руководителем"
            )

        return recommendations

    def _extract_feedback_text(self, reviews: List, respondent_reviews: List) -> str:
        """Извлечение текста из всех отзывов"""
        all_text = ""

        for review in reviews:
            # Самооценка
            if review.self_evaluation_answers:
                try:
                    answers = json.loads(review.self_evaluation_answers)
                    all_text += " " + " ".join([a.get("answer", "") for a in answers])
                except:
                    pass

            # Оценка руководителя
            if review.manager_evaluation_answers:
                try:
                    answers = json.loads(review.manager_evaluation_answers)
                    all_text += " " + " ".join([a.get("answer", "") for a in answers])
                except:
                    pass

            # Обратная связь руководителя
            if review.final_feedback:
                all_text += " " + review.final_feedback

        # Комментарии респондентов
        for resp_review in respondent_reviews:
            if resp_review.comments:
                all_text += " " + resp_review.comments

        return all_text.lower()

    def get_employee_summary(self, employee_id: str) -> Dict[str, Any]:
        """Сводная аналитика по всем целям сотрудника"""

        goals = self.db.query(Goal).filter(Goal.employee_id == employee_id).all()

        goal_analytics = []
        total_score = 0
        goal_count = 0

        for goal in goals:
            analytics = self.get_goal_analytics(goal.id)  # type: ignore
            goal_analytics.append(analytics)

            if analytics.get("scores", {}).get("total_score", 0) > 0:
                total_score += analytics["scores"]["total_score"]
                goal_count += 1

        avg_score = total_score / goal_count if goal_count > 0 else 0

        return {
            "employee_id": employee_id,
            "total_goals": len(goals),
            "completed_goals": len([g for g in goals if g.status == "completed"]),  # type: ignore
            "average_score": round(avg_score, 2),
            "overall_rating": self._calculate_final_rating(avg_score),
            "goals_analytics": goal_analytics,
        }

    def _calculate_review_score(
        self, review: Review, review_service: ReviewService
    ) -> float:
        """Расчет балла с учетом вопросов, оцененных руководителем"""
        answers = self._get_all_answers(review)

        # Проверяем, все ли вопросы оценены
        if review_service.has_pending_manager_scores(review.id):  # type: ignore
            logger.warning(f"Review {review.id} has pending manager scores")

        return review_service.calculate_weighted_score(answers, review.review_type)  # type: ignore

    def _get_all_answers(self, review: Review) -> List[Answer]:
        """Получить все ответы из оценки"""
        answers_data = []

        if review.review_type == ReviewType.SELF and review.self_evaluation_answers:  # type: ignore
            answers_data = json.loads(review.self_evaluation_answers)  # type: ignore
        elif review.review_type == ReviewType.MANAGER and review.manager_evaluation_answers:  # type: ignore
            answers_data = json.loads(review.manager_evaluation_answers)  # type: ignore
        elif review.review_type == ReviewType.POTENTIAL and review.potential_evaluation_answers:  # type: ignore
            answers_data = json.loads(review.potential_evaluation_answers)  # type: ignore
        elif review.review_type == ReviewType.RESPONDENT and hasattr(review, "answers"):  # type: ignore
            answers_data = json.loads(review.answers)  # type: ignore

        return [Answer(**data) for data in answers_data]
