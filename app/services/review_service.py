from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
from app.models.schemas import Answer, ReviewType
from app.models.database import QuestionTemplate, Review
from app.core.logger import logger

class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_question_by_id(self, question_id: str) -> QuestionTemplate:
        """Получение вопроса по ID"""
        return self.db.query(QuestionTemplate).filter(
            QuestionTemplate.id == question_id,
            QuestionTemplate.is_active == True
        ).first() # type: ignore

    def calculate_weighted_score(self, answers: List[Answer], review_type: str) -> float:
        """Расчет взвешенного балла с учетом вопросов, требующих оценки руководителя"""
        if not answers:
            return 0.0

        total_weighted_score = 0.0
        total_weight = 0.0
        pending_manager_scores = 0

        for answer in answers:
            question = self.get_question_by_id(answer.question_id)
            
            if not question:
                continue

            # ВОПРОСЫ, ТРЕБУЮЩИЕ ОЦЕНКИ РУКОВОДИТЕЛЯ
            if question.requires_manager_scoring: # type: ignore
                if answer.score is not None:
                    # Руководитель уже оценил - учитываем в расчете
                    normalized_score = (answer.score / question.max_score) * 5.0
                    total_weighted_score += normalized_score * question.weight
                    total_weight += question.weight
                else:
                    # Ожидаем оценку руководителя - не учитываем
                    pending_manager_scores += 1
                    logger.info(f"Pending manager score for question {question.id}")

            # ОБЫЧНЫЕ ВОПРОСЫ С ОЦЕНКОЙ
            elif question.max_score > 0 and answer.score is not None: # type: ignore
                normalized_score = (answer.score / question.max_score) * 5.0
                total_weighted_score += normalized_score * question.weight
                total_weight += question.weight

            # ВОПРОСЫ С ВАРИАНТАМИ ОТВЕТОВ
            elif question.options_json and answer.selected_option: # type: ignore
                option_score = self._get_option_score(question, answer.selected_option)
                if option_score is not None:
                    normalized_score = (option_score / question.max_score) * 5.0
                    total_weighted_score += normalized_score * question.weight
                    total_weight += question.weight

        # Логируем предупреждение о неоцененных вопросах
        if pending_manager_scores > 0:
            logger.warning(f"Found {pending_manager_scores} questions pending manager scoring")

        return total_weighted_score / total_weight if total_weight > 0 else 0.0 # type: ignore

    # ДОБАВИТЬ новые методы:
    def get_pending_manager_scoring_questions(self, review_id: str) -> List[Dict]:
        """Получить вопросы, ожидающие оценку руководителя"""
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            return []

        pending_questions = []
        answers_data = []

        # Получаем ответы в зависимости от типа оценки
        if review.review_type == ReviewType.SELF and review.self_evaluation_answers: # type: ignore
            answers_data = json.loads(review.self_evaluation_answers) # type: ignore
        elif review.review_type == ReviewType.MANAGER and review.manager_evaluation_answers: # type: ignore
            answers_data = json.loads(review.manager_evaluation_answers) # type: ignore
        elif review.review_type == ReviewType.RESPONDENT and hasattr(review, 'answers'): # type: ignore
            answers_data = json.loads(review.answers) # type: ignore
        for answer_data in answers_data:
            question = self.get_question_by_id(answer_data.get("question_id"))
            if (question and 
                question.requires_manager_scoring and 
                answer_data.get("score") is None): # type: ignore
                
                pending_questions.append({
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "answer_text": answer_data.get("answer", ""),
                    "max_score": question.max_score,
                    "weight": question.weight,
                    "section": question.section
                })

        return pending_questions

    def has_pending_manager_scores(self, review_id: str) -> bool:
        """Проверить, есть ли вопросы, ожидающие оценку руководителя"""
        return len(self.get_pending_manager_scoring_questions(review_id)) > 0

    def calculate_review_score(self, answers: List[Answer], review_type: str) -> float:
        """Основной метод расчета баллов (для обратной совместимости)"""
        return self.calculate_weighted_score(answers, review_type)

    def calculate_potential_score(self, answers: List[Answer]) -> Dict[str, float]:
        """Расчет оценки потенциала по компонентам"""
        professional_score = 0.0
        personal_score = 0.0
        development_score = 0.0
        
        professional_weight = 0.0
        personal_weight = 0.0
        development_weight = 0.0

        for answer in answers:
            question = self.get_question_by_id(answer.question_id)
            
            if question and answer.score is not None:
                normalized_score = (answer.score / question.max_score) * 5.0
                
                if question.section == "professional": # type: ignore
                    professional_score += normalized_score * question.weight
                    professional_weight += question.weight
                elif question.section == "personal": # type: ignore
                    personal_score += normalized_score * question.weight
                    personal_weight += question.weight
                elif question.section == "development": # type: ignore
                    development_score += normalized_score * question.weight
                    development_weight += question.weight

        # Рассчитываем средние баллы для каждого раздела
        professional_avg = professional_score / professional_weight if professional_weight > 0 else 0.0 # type: ignore
        personal_avg = personal_score / personal_weight if personal_weight > 0 else 0.0 # type: ignore
        development_avg = development_score / development_weight if development_weight > 0 else 0.0 # type: ignore

        # Общий балл потенциала (взвешенное среднее)
        total_potential_score = (
            professional_avg * 0.4 +  # Профессиональные качества - 40%
            personal_avg * 0.3 +      # Личные качества - 30%
            development_avg * 0.3     # Стремление развиваться - 30%
        ) * 2.0  # Приводим к шкале 0-10

        return {
            "professional_score": round(professional_avg * 2.0, 2), # type: ignore
            "personal_score": round(personal_avg * 2.0, 2), # type: ignore
            "development_score": round(development_avg * 2.0, 2), # type: ignore
            "total_potential_score": round(total_potential_score, 2), # type: ignore
            "performance_score": self.calculate_weighted_score(answers, "potential")  # Результативность
        }

    def extract_trigger_words_feedback(self, answers: List[Answer]) -> List[str]:
        """Извлечение триггерных слов из ответов для рекомендаций"""
        all_feedback_text = ""
        
        for answer in answers:
            # Предполагаем, что answer.answer содержит текстовый ответ
            if hasattr(answer, 'answer') and answer.answer:
                all_feedback_text += " " + answer.answer.lower()

        # Получаем все триггерные слова из вопросов
        trigger_words_map = {}
        for answer in answers:
            question = self.get_question_by_id(answer.question_id)
            if question and question.trigger_words: # type: ignore
                try:
                    words = json.loads(question.trigger_words) # type: ignore
                    trigger_words_map[question.section or "general"] = words
                except:
                    continue

        # Анализируем текст на наличие триггерных слов
        recommendations = self._generate_recommendations_from_triggers(
            all_feedback_text, 
            trigger_words_map
        )

        return recommendations

    def _generate_recommendations_from_triggers(self, text: str, trigger_words_map: Dict) -> List[str]:
        """Генерация рекомендаций на основе триггерных слов"""
        recommendations = []

        # Словарь триггеров и соответствующих рекомендаций
        trigger_recommendations = {
            "problem": [
                "Рекомендуется тренировка навыков решения сложных задач",
                "Развитие стрессоустойчивости и адаптивности"
            ],
            "communication": [
                "Улучшение навыков коммуникации и работы в команде",
                "Тренировка презентационных навыков"
            ],
            "leadership": [
                "Развитие лидерских качеств и управления командой",
                "Обучение делегированию задач"
            ],
            "development": [
                "Разработка индивидуального плана развития",
                "Участие в программах менторства"
            ],
            "success": [
                "Развитие навыков управления успешными проектами",
                "Обучение стратегическому планированию"
            ]
        }

        # Проверяем наличие триггерных слов в тексте
        for section, words in trigger_words_map.items():
            for word in words:
                if word in text:
                    # Добавляем соответствующие рекомендации
                    if "сложн" in word or "проблем" in word or "трудн" in word:
                        recommendations.extend(trigger_recommendations["problem"])
                    elif "коммуник" in word or "общен" in word or "команд" in word:
                        recommendations.extend(trigger_recommendations["communication"])
                    elif "лидер" in word or "руковод" in word:
                        recommendations.extend(trigger_recommendations["leadership"])
                    elif "развит" in word or "рост" in word:
                        recommendations.extend(trigger_recommendations["development"])
                    elif "успех" in word or "результат" in word:
                        recommendations.extend(trigger_recommendations["success"])

        # Убираем дубликаты
        unique_recommendations = list(set(recommendations))
        
        # Если нет специфических рекомендаций, даем общую
        if not unique_recommendations:
            unique_recommendations = [
                "Рекомендуется индивидуальная консультация с руководителем"
            ]

        return unique_recommendations[:5]  # Возвращаем не более 5 рекомендаций

    def calculate_final_rating(self, total_score: float) -> str:
        """Определение итогового рейтинга на основе балла (шкала 0-5)"""
        if total_score >= 4.5:
            return "A"
        elif total_score >= 4.0:
            return "B"
        elif total_score >= 3.0:
            return "C"
        else:
            return "D"
        
    def _get_option_score(self, question: QuestionTemplate, selected_option_id: str) -> Optional[float]:
        """Получить балл за выбранный вариант ответа"""
        try:
            if question.options_json: # type: ignore
                options = json.loads(question.options_json) # type: ignore
                for option in options:
                    if option.get("id") == selected_option_id:
                        return option.get("value", 0.0)
        except Exception as e:
            logger.error(f"Error getting option score: {e}")
        return None