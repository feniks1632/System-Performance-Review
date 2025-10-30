"""
Скрипт для инициализации вопросов по умолчанию в системе
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logger import logger
from app.database.session import SessionLocal
from app.models.database import QuestionTemplate


def init_default_questions():
    """Инициализация вопросов по умолчанию"""
    db = SessionLocal()

    try:
        logger.info("Начинаем инициализацию вопросов по умолчанию...")

        # Проверяем, есть ли уже вопросы
        existing_count = (
            db.query(QuestionTemplate)
            .filter(QuestionTemplate.is_active == True)
            .count()
        )
        if existing_count > 0:
            logger.info("Вопросы уже существуют в системе. Пропускаем инициализацию.")
            return

        # Вопросы для самооценки (из гугл таблиц)
        self_evaluation_questions = [
            {
                "question_text": "Впиши, используя шаблон, каких результатов удалось достичь (пример: выявил возможность оптимизации количества кликов при оформлении подписки и после реализации улучшения рост по оплате подписки составил +1%)",
                "question_type": "self",
                "section": "achievements",
                "weight": 1.5,
                "max_score": 10,
                "order_index": 1,
                "trigger_words": json.dumps(
                    ["достижен", "результат", "успех", "рост", "улучшен", "оптимизац"]
                ),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Какой личный вклад ты сделал в полученный результат (пример: благодаря созданной документации команда находила решения в 1,5 раза быстрее)",
                "question_type": "self",
                "section": "personal_contribution",
                "weight": 1.3,
                "max_score": 10,
                "order_index": 2,
                "trigger_words": json.dumps(
                    ["вклад", "личный", "инициатив", "ответствен"]
                ),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Что ты забираешь с собой по результатам выполнения этой задачи (например: прокачался в микросервисах, хочу это развивать дальше)",
                "question_type": "self",
                "section": "skills_development",
                "weight": 1.2,
                "max_score": 10,
                "order_index": 3,
                "trigger_words": json.dumps(["развит", "навыки", "обучен", "план"]),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Что в следующий раз будешь делать по-другому",
                "question_type": "self",
                "section": "improvements",
                "weight": 1.1,
                "max_score": 10,
                "order_index": 4,
                "trigger_words": json.dumps(["улучшен", "изменен", "опыт", "ошибк"]),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Как ты оцениваешь качество своего взаимодействия с коллегами, командой по данной задаче",
                "question_type": "self",
                "section": "communication",
                "weight": 1.1,
                "max_score": 10,
                "order_index": 5,
                "trigger_words": json.dumps(
                    ["коммуникац", "взаимодейств", "общен", "команд"]
                ),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Как ты оцениваешь общую удовлетворенность своим выполнением данной задачи",
                "question_type": "self",
                "section": "satisfaction",
                "weight": 1.1,
                "max_score": 10,
                "order_index": 6,
                "trigger_words": json.dumps(
                    ["удовлетворен", "оценка", "результат", "выполнен"]
                ),
                "options_json": None,
                "requires_manager_scoring": False,
            },
        ]

        # Вопросы для оценки руководителя (из гугл таблиц)
        manager_evaluation_questions = [
            {
                "question_text": "Насколько удалось сотруднику достичь результатов, которые были запланированы по задаче",
                "question_type": "manager",
                "section": "results_achievement",
                "weight": 2.0,
                "max_score": 10,
                "order_index": 1,
                "trigger_words": json.dumps(["результат", "достижен", "план", "KPI"]),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Прокомментируй, какие личные качества помогли сотруднику достичь результата",
                "question_type": "manager",
                "section": "personal_qualities",
                "weight": 1.5,
                "max_score": 10,  # Текстовая оценка - балл не нужен
                "order_index": 2,
                "trigger_words": json.dumps(
                    ["качества", "личные", "ответствен", "инициатив"]
                ),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Какой личный вклад ты можешь выделить в результатах сотрудника",
                "question_type": "manager",
                "section": "personal_contribution",
                "weight": 1.5,
                "max_score": 10,  # Текстовая оценка - балл не нужен
                "order_index": 3,
                "trigger_words": json.dumps(
                    ["вклад", "результат", "влияние", "ценность"]
                ),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Оцени качество взаимодействия по общей оценке коллег",
                "question_type": "manager",
                "section": "communication",
                "weight": 1.3,
                "max_score": 10,
                "order_index": 4,
                "trigger_words": json.dumps(
                    ["коммуникац", "взаимодейств", "команд", "общен"]
                ),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Что ты порекомендуешь улучшить сотруднику в следующем цикле",
                "question_type": "manager",
                "section": "improvement_recommendations",
                "weight": 1.4,
                "max_score": 10,  # Текстовая оценка - балл не нужен
                "order_index": 5,
                "trigger_words": json.dumps(
                    ["улучшен", "рекомендац", "развит", "рост"]
                ),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Какой общий рейтинг ты можешь выделить для сотрудника",
                "question_type": "manager",
                "section": "final_rating",
                "weight": 1.4,
                "max_score": 10,
                "order_index": 6,
                "trigger_words": json.dumps(["рейтинг", "оценка", "итог", "результат"]),
                "options_json": None,
                "requires_manager_scoring": False,
            },
        ]

        # Вопросы для оценки потенциала (из гугл таблиц)
        potential_evaluation_questions = [
            # Профессиональные качества
            {
                "question_text": "Какие профессиональные качества проявил сотрудник за последний период работы",
                "question_type": "potential",
                "section": "professional",
                "weight": 1.8,
                "max_score": 5,
                "order_index": 1,
                "trigger_words": json.dumps(
                    ["профессионал", "качества", "навыки", "компетенц"]
                ),
                "options_json": json.dumps(
                    [
                        {
                            "id": "responsibility",
                            "text": "Ответственность",
                            "value": 1.0,
                            "order_index": 1,
                        },
                        {
                            "id": "result_oriented",
                            "text": "Ориентация на результат",
                            "value": 1.0,
                            "order_index": 2,
                        },
                        {
                            "id": "proactive",
                            "text": "Проактивность (исследовал решение глубже, чем ожидалось)",
                            "value": 1.0,
                            "order_index": 3,
                        },
                        {
                            "id": "strategic_thinking",
                            "text": "Стратегическое мышление (нестандартное мышление) - тестировал новые подходы",
                            "value": 1.0,
                            "order_index": 4,
                        },
                        {
                            "id": "team_player",
                            "text": "Командный игрок (объединял команду, вел за собой)",
                            "value": 1.0,
                            "order_index": 5,
                        },
                    ]
                ),
                "requires_manager_scoring": False,
            },
            # Личные качества
            {
                "question_text": "Какие личные качества проявил сотрудник за последний период работы",
                "question_type": "potential",
                "section": "personal",
                "weight": 1.3,
                "max_score": 4,
                "order_index": 2,
                "trigger_words": json.dumps(["личные", "качества", "характер"]),
                "options_json": json.dumps(
                    [
                        {
                            "id": "more_responsibility",
                            "text": "Не боялся брать на себя больше ответственности в задаче",
                            "value": 1.0,
                            "order_index": 1,
                        },
                        {
                            "id": "good_communication",
                            "text": "Выстраивал открытую прозрачную и точную коммуникацию с коллегами",
                            "value": 1.0,
                            "order_index": 2,
                        },
                        {
                            "id": "information_sharing",
                            "text": "Оперативно делился информацией о задаче с коллегами",
                            "value": 1.0,
                            "order_index": 3,
                        },
                        {
                            "id": "task_organization",
                            "text": "Выстраивал работу по задаче",
                            "value": 1.0,
                            "order_index": 4,
                        },
                    ]
                ),
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Приходилось ли тебе за последние полгода проводить 1:1, на котором нужно было мотивировать сотрудника дополнительно по уже реализуемой задаче",
                "question_type": "potential",
                "section": "management_intervention",
                "weight": 1.0,
                "max_score": 1,
                "order_index": 3,
                "trigger_words": json.dumps(
                    ["мотивац", "1:1", "дополнительн", "руководств"]
                ),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Знаешь ли ты о случаях, когда сотрудник не делился дискоммуникацией с другими коллегами и это негативно сказывалось на результатах",
                "question_type": "potential",
                "section": "communication_issues",
                "weight": 1.0,
                "max_score": 1,
                "order_index": 4,
                "trigger_words": json.dumps(
                    ["информац", "проблем", "негатив", "результат"]
                ),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Знаешь ли ты о желании сотрудника развиваться дальше (в каком треке, какие роли интересны)",
                "question_type": "potential",
                "section": "development_aspiration",
                "weight": 1.0,
                "max_score": 4,
                "order_index": 5,
                "trigger_words": json.dumps(["развит", "трек", "роли", "интерес"]),
                "options_json": json.dumps(
                    [
                        {
                            "id": "proactive_development",
                            "text": "Да, хочет развиваться и проактивно себя ведет",
                            "value": 4.0,
                            "order_index": 1,
                        },
                        {
                            "id": "needs_help_development",
                            "text": "Да, хочет развиваться, но сам не может идти по плану развития, нужна помощь менеджера/HR",
                            "value": 3.0,
                            "order_index": 2,
                        },
                        {
                            "id": "unsure_development",
                            "text": "Не уверен, что есть желание развиваться",
                            "value": 2.0,
                            "order_index": 3,
                        },
                        {
                            "id": "no_development",
                            "text": "Не хочет",
                            "value": 1.0,
                            "order_index": 4,
                        },
                    ]
                ),
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Считаешь ли ты сотрудника своим преемником",
                "question_type": "potential",
                "section": "succession",
                "weight": 1.0,
                "max_score": 1,
                "order_index": 6,
                "trigger_words": json.dumps(["преемник", "замена", "продолжен"]),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Если да, когда он будет готов",
                "question_type": "potential",
                "section": "succession_timing",
                "weight": 1.0,
                "max_score": 3,
                "order_index": 7,
                "trigger_words": json.dumps(["готов", "срок", "время", "план"]),
                "options_json": json.dumps(
                    [
                        {
                            "id": "ready_1_2_years",
                            "text": "через 1-2 года",
                            "value": 3.0,
                            "order_index": 1,
                        },
                        {
                            "id": "ready_3_years",
                            "text": "через 3 года",
                            "value": 2.0,
                            "order_index": 2,
                        },
                        {
                            "id": "ready_3_plus_years",
                            "text": "через 3 и более лет",
                            "value": 1.0,
                            "order_index": 3,
                        },
                    ]
                ),
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Как ты оцениваешь степень риска ухода сотрудника, где 0 - нет риска, 10 - высокая степень риска ухода даже в этом году",
                "question_type": "potential",
                "section": "retention_risk",
                "weight": 1.0,
                "max_score": 10,
                "order_index": 8,
                "trigger_words": json.dumps(["риск", "уход", "удержан", "лояльност"]),
                "options_json": None,
                "requires_manager_scoring": False,
            },
        ]

        # Вопросы для оценки респондентов
        respondent_evaluation_questions = [
            {
                "question_text": "Насколько удалось сотруднику достичь результатов, которые были запланированы по задаче",
                "question_type": "respondent",
                "section": "results_achievement",
                "weight": 1.5,
                "max_score": 10,
                "order_index": 1,
                "trigger_words": json.dumps(["результат", "достижен", "план"]),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Прокомментируй, какие личные качества помогли достичь результата",
                "question_type": "respondent",
                "section": "personal_qualities",
                "weight": 1.2,
                "max_score": 10,  # Текстовая оценка
                "order_index": 2,
                "trigger_words": json.dumps(["качества", "личные", "помогл"]),
                "options_json": None,
                "requires_manager_scoring": True,
            },
            {
                "question_text": "Оцени качество взаимодействия",
                "question_type": "respondent",
                "section": "communication",
                "weight": 1.3,
                "max_score": 10,
                "order_index": 3,
                "trigger_words": json.dumps(["взаимодейств", "коммуникац", "качество"]),
                "options_json": None,
                "requires_manager_scoring": False,
            },
            {
                "question_text": "Что сотрудник может улучшить в своей работе в следующем полугодии",
                "question_type": "respondent",
                "section": "improvements",
                "weight": 1.1,
                "max_score": 10,  # Текстовая оценка
                "order_index": 4,
                "trigger_words": json.dumps(["улучшен", "рекомендац", "совет"]),
                "options_json": None,
                "requires_manager_scoring": True,
            },
        ]

        # Объединяем все вопросы
        all_questions = (
            self_evaluation_questions
            + manager_evaluation_questions
            + potential_evaluation_questions
            + respondent_evaluation_questions
        )

        # Создаем вопросы в БД
        questions = []
        for q_data in all_questions:
            question = QuestionTemplate(
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                section=q_data["section"],
                weight=q_data["weight"],
                max_score=q_data["max_score"],
                trigger_words=q_data["trigger_words"],
                order_index=q_data["order_index"],
                options_json=q_data.get("options_json"),
                requires_manager_scoring=q_data.get("requires_manager_scoring", False),
            )
            questions.append(question)

        db.add_all(questions)
        db.commit()

        logger.info("Вопросы по умолчанию успешно созданы!")
        logger.info("Статистика:")
        logger.info("- Самооценка: %d вопросов", len(self_evaluation_questions))
        logger.info(
            "- Оценка руководителя: %d вопросов", len(manager_evaluation_questions)
        )
        logger.info(
            "- Оценка потенциала: %d вопросов", len(potential_evaluation_questions)
        )
        logger.info(
            "- Оценка респондентов: %d вопросов", len(respondent_evaluation_questions)
        )
        logger.info("- Всего: %d вопросов", len(all_questions))

    except Exception as e:
        logger.error("Ошибка при создании вопросов по умолчанию: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_default_questions()
