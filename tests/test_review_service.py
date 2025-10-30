import pytest
from unittest.mock import Mock, patch
from app.services.review_service import ReviewService
from app.models.schemas import Answer, ReviewType
from app.models.database import QuestionTemplate


class TestReviewService:

    def test_calculate_weighted_score_basic(self, db_session):
        """Тест базового расчета взвешенного балла"""
        # Создаем тестовый вопрос
        question = QuestionTemplate(
            question_text="Тестовый вопрос",
            question_type="self",
            weight=1.0,
            max_score=5,
        )
        db_session.add(question)
        db_session.commit()

        # Создаем ответы
        answers = [
            Answer(question_id=question.id, score=4.0)  # type:ignore
        ]

        service = ReviewService(db_session)
        score = service.calculate_weighted_score(answers, "self")

        # Ожидаемый результат: (4.0 / 5 * 5) * 1.0 / 1.0 = 4.0
        expected_score = 4.0
        assert (
            abs(score - expected_score) < 0.01
        ), f"Expected {expected_score}, got {score}"

    def test_calculate_weighted_score_multiple_questions(self, db_session):
        """Тест расчета с несколькими вопросами разных весов"""
        # Создаем вопросы с разными весами
        question1 = QuestionTemplate(
            question_text="Вопрос 1", question_type="self", weight=1.0, max_score=5
        )
        question2 = QuestionTemplate(
            question_text="Вопрос 2", question_type="self", weight=2.0, max_score=10
        )
        db_session.add_all([question1, question2])
        db_session.commit()

        # Создаем ответы
        answers = [
            Answer(
                question_id=question1.id, score=4 # type:ignore
            ),  # 4/5 * 5 = 4.0 * 1.0 = 4.0 # type:ignore
            Answer(
                question_id=question2.id, score=8 # type:ignore
            ),  # 8/10 * 5 = 4.0 * 2.0 = 8.0 # type:ignore
        ]

        service = ReviewService(db_session)
        score = service.calculate_weighted_score(answers, "self")

        # Ожидаемый: (4.0 + 8.0) / (1.0 + 2.0) = 12.0 / 3.0 = 4.0
        expected_score = 4.0
        assert (
            abs(score - expected_score) < 0.01
        ), f"Expected {expected_score}, got {score}"

    def test_calculate_weighted_score_no_answers(self, db_session):
        """Тест расчета с пустым списком ответов"""
        service = ReviewService(db_session)
        score = service.calculate_weighted_score([], "self")
        assert score == 0.0

    def test_calculate_weighted_score_with_normalization(self, db_session):
        """Тест нормализации баллов для разных шкал"""
        # Вопрос с max_score=5
        question1 = QuestionTemplate(
            question_text="Вопрос по 5-балльной шкале",
            question_type="self",
            weight=1.0,
            max_score=5,
        )
        # Вопрос с max_score=10
        question2 = QuestionTemplate(
            question_text="Вопрос по 10-балльной шкале",
            question_type="self",
            weight=1.0,
            max_score=10,
        )
        db_session.add_all([question1, question2])
        db_session.commit()

        # Ответы с одинаковыми "процентами" выполнения
        answers = [
            Answer(
                question_id=question1.id, score=4 # type:ignore
            ),  # 4/5 = 80% → 4.0 в 5-балльной # type:ignore
            Answer(
                question_id=question2.id, score=8 # type:ignore
            ),  # 8/10 = 80% → 4.0 в 5-балльной # type:ignore
        ]

        service = ReviewService(db_session)
        score = service.calculate_weighted_score(answers, "self")

        # Оба ответа должны дать 4.0 после нормализации
        expected_score = 4.0
        assert (
            abs(score - expected_score) < 0.01
        ), f"Expected {expected_score}, got {score}"

    def test_calculate_potential_score(self, db_session):
        """Тест расчета оценки потенциала"""
        # Создаем вопросы для разных разделов потенциала
        professional_question = QuestionTemplate(
            question_text="Профессиональные навыки",
            question_type="potential",
            section="professional",
            weight=1.5,
            max_score=5,
        )

        personal_question = QuestionTemplate(
            question_text="Личные качества",
            question_type="potential",
            section="personal",
            weight=1.0,
            max_score=5,
        )

        development_question = QuestionTemplate(
            question_text="Стремление к развитию",
            question_type="potential",
            section="development",
            weight=1.0,
            max_score=5,
        )

        db_session.add_all(
            [professional_question, personal_question, development_question]
        )
        db_session.commit()

        # Создаем ответы
        answers = [
            Answer(
                question_id=professional_question.id, score=4 # type:ignore
            ),  # professional: 4/5*5=4.0 # type:ignore
            Answer(
                question_id=personal_question.id, score=3 # type:ignore
            ),  # personal: 3/5*5=3.0 # type:ignore
            Answer(
                question_id=development_question.id, score=5 # type:ignore
            ),  # development: 5/5*5=5.0 # type:ignore
        ]

        service = ReviewService(db_session)
        potential_scores = service.calculate_potential_score(answers)

        # Проверяем структуру ответа
        required_keys = [
            "professional_score",
            "personal_score",
            "development_score",
            "total_potential_score",
            "performance_score",
        ]
        for key in required_keys:
            assert key in potential_scores, f"Missing key: {key}"

        # Проверяем расчет профессионального балла
        # professional: (4.0 * 1.5) / 1.5 = 4.0 * 2.0 = 8.0
        assert potential_scores["professional_score"] == 8.0

        # Проверяем что все баллы рассчитаны
        assert potential_scores["professional_score"] > 0
        assert potential_scores["personal_score"] > 0
        assert potential_scores["development_score"] > 0
        assert potential_scores["total_potential_score"] > 0

    def test_extract_trigger_words_feedback(self, db_session):
        """Тест извлечения триггерных слов из ответов"""
        # Создаем вопрос с триггерными словами
        question = QuestionTemplate(
            question_text="Опишите сложности",
            question_type="self",
            trigger_words='["сложн", "проблем", "трудн"]',
        )
        db_session.add(question)
        db_session.commit()

        # Создаем ответ с триггерными словами
        answers = [
            Answer(
                question_id=question.id,  # type:ignore
                answer="В работе возникли сложности и проблемы с интеграцией",
                score=3,
            )
        ]

        service = ReviewService(db_session)
        recommendations = service.extract_trigger_words_feedback(answers)

        # Должны быть рекомендации по решению проблем
        assert len(recommendations) > 0
        assert any("сложных задач" in rec for rec in recommendations)

    def test_calculate_final_rating(self, db_session):
        """Тест определения итогового рейтинга"""
        service = ReviewService(db_session)

        # Тестируем граничные значения (шкала 0-5 после исправления)
        assert service.calculate_final_rating(4.5) == "A"  # >= 4.5
        assert service.calculate_final_rating(4.0) == "B"  # >= 4.0
        assert service.calculate_final_rating(3.0) == "C"  # >= 3.0
        assert service.calculate_final_rating(2.9) == "D"  # < 3.0
        assert service.calculate_final_rating(0.0) == "D"

    def test_get_question_by_id(self, db_session):
        """Тест получения вопроса по ID"""
        # Создаем вопрос
        question = QuestionTemplate(
            question_text="Тестовый вопрос",
            question_type="self",
            weight=1.0,
            max_score=5,
        )
        db_session.add(question)
        db_session.commit()

        service = ReviewService(db_session)
        found_question = service.get_question_by_id(question.id)  # type:ignore

        assert found_question is not None
        assert found_question.id == question.id  # type:ignore
        assert found_question.question_text == "Тестовый вопрос"  # type:ignore

    def test_get_question_by_id_not_found(self, db_session):
        """Тест получения несуществующего вопроса"""
        service = ReviewService(db_session)
        found_question = service.get_question_by_id("non-existent-id")
        assert found_question is None
