import pytest
from datetime import datetime, timedelta


def test_calculate_scores_empty_data(analytics_service):
    """Тест расчета баллов с пустыми данными"""
    scores = analytics_service._calculate_scores([], [])

    assert scores["self_score"] == 0
    assert scores["manager_score"] == 0
    assert scores["respondent_score"] == 0
    assert scores["total_score"] == 0


def test_calculate_final_rating(analytics_service):
    """Тест расчета итогового рейтинга"""
    # A рейтинг
    assert analytics_service._calculate_final_rating(4.8) == "A"
    assert analytics_service._calculate_final_rating(4.5) == "A"

    # B рейтинг
    assert analytics_service._calculate_final_rating(4.4) == "B"
    assert analytics_service._calculate_final_rating(4.0) == "B"

    # C рейтинг
    assert analytics_service._calculate_final_rating(3.9) == "C"
    assert analytics_service._calculate_final_rating(3.0) == "C"

    # D рейтинг
    assert analytics_service._calculate_final_rating(2.9) == "D"
    assert analytics_service._calculate_final_rating(0.0) == "D"


def test_generate_recommendations_with_feedback(analytics_service):
    """Тест генерации рекомендаций на основе фидбека"""

    class MockReview:
        def __init__(self):
            self.self_evaluation_answers = (
                '[{"answer": "Было очень сложно выполнить задачу"}]'
            )
            self.manager_evaluation_answers = None
            self.potential_evaluation_answers = None
            self.final_feedback = None

    class MockRespondentReview:
        def __init__(self):
            self.answers = "[]"
            self.comments = "Сотрудник испытывал трудности"

    reviews = [MockReview()]
    respondent_reviews = [MockRespondentReview()]

    recommendations = analytics_service._generate_recommendations(
        reviews, respondent_reviews
    )

    assert len(recommendations) > 0
    assert "тренировка навыков" in recommendations[0].lower()


def test_extract_feedback_text(analytics_service):
    """Тест извлечения текста из фидбека"""

    class MockReview:
        def __init__(self):
            self.self_evaluation_answers = '[{"answer": "Хорошая работа"}]'
            self.manager_evaluation_answers = '[{"answer": "Отличные результаты"}]'
            self.final_feedback = "Продолжайте в том же духе"

    class MockRespondentReview:
        def __init__(self):
            self.comments = "Отличный сотрудник"

    reviews = [MockReview()]
    respondent_reviews = [MockRespondentReview()]

    text = analytics_service._extract_feedback_text(reviews, respondent_reviews)

    assert "хорошая работа" in text
    assert "отличные результаты" in text
    assert "продолжайте в том же духе" in text
    assert "отличный сотрудник" in text
