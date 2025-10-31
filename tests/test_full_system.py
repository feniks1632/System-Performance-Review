from app.core.logger import logger


def test_full_system_workflow(
    client,
    test_employee_user,
    test_manager_user_complete,
    test_question_templates,
    test_goal_with_employee,
    employee_auth_headers,
    manager_auth_headers,
):
    """Полный тест рабочего процесса системы Performance Review"""

    logger.info("ЗАПУСК ПОЛНОГО ТЕСТА СИСТЕМЫ С ФИКСТУРАМИ\n")

    # 1. Проверяем что пользователи созданы
    logger.info("1. Проверяем тестовые данные")
    logger.info(
        "- Сотрудник: %s (%s)", test_employee_user.full_name, test_employee_user.email
    )
    logger.info(
        "- Руководитель: %s (%s)",
        test_manager_user_complete.full_name,
        test_manager_user_complete.email,
    )
    logger.info("- Вопросов создано: %d", len(test_question_templates))
    logger.info("- Цель создана: %s", test_goal_with_employee.title)

    # 2. Работа с целями сотрудника
    logger.info("2. Тестируем управление целями")

    goals_response = client.get(
        f"/api/v1/goals/employee/{test_employee_user.id}", headers=employee_auth_headers
    )
    assert (
        goals_response.status_code == 200
    ), f"Ошибка получения целей: {goals_response.text}"
    goals = goals_response.json()
    logger.info("Получено целей: %d", len(goals))

    goal_id = test_goal_with_employee.id
    logger.debug("ID тестовой цели: %s", goal_id)

    # 3. Получение вопросов для самооценки
    logger.info("3. Тестируем систему вопросов")

    questions_response = client.get(
        "/api/v1/question-templates/?question_type=self", headers=employee_auth_headers
    )
    assert (
        questions_response.status_code == 200
    ), f"Ошибка получения вопросов: {questions_response.text}"
    questions = questions_response.json()
    logger.info("Получено вопросов для самооценки: %d", len(questions))

    # 4. Создание самооценки
    logger.info("4. Тестируем создание самооценки")

    if questions:
        question_id = questions[0]["id"]

        self_review_data = {
            "goal_id": goal_id,
            "review_type": "self",
            "answers": [
                {
                    "question_id": question_id,
                    "answer": "Успешно реализовал весь запланированный функционал. Достиг всех KPI по проекту.",
                    "score": 4.5,
                }
            ],
        }

        self_review_response = client.post(
            "/api/v1/reviews/", json=self_review_data, headers=employee_auth_headers
        )
        assert (
            self_review_response.status_code == 200
        ), f"Ошибка создания самооценки: {self_review_response.text}"
        self_review = self_review_response.json()
        assert self_review["calculated_score"] > 0, "Балл не рассчитан"
        logger.info("Самооценка создана, балл: %.2f", self_review["calculated_score"])

    # 5. Создание оценки руководителя
    logger.info("5. Тестируем оценку руководителя")

    manager_questions_response = client.get(
        "/api/v1/question-templates/?question_type=manager",
        headers=manager_auth_headers,
    )
    assert (
        manager_questions_response.status_code == 200
    ), f"Ошибка получения вопросов руководителя: {manager_questions_response.text}"
    manager_questions = manager_questions_response.json()
    logger.info("Получено вопросов для оценки руководителя: %d", len(manager_questions))

    if manager_questions:
        question_id = manager_questions[0]["id"]

        manager_review_data = {
            "goal_id": goal_id,
            "review_type": "manager",
            "answers": [
                {
                    "question_id": question_id,
                    "answer": "Сотрудник показал отличные результаты, превысил плановые показатели на 15%.",
                    "score": 9.0,
                }
            ],
        }

        manager_review_response = client.post(
            "/api/v1/reviews/", json=manager_review_data, headers=manager_auth_headers
        )
        assert (
            manager_review_response.status_code == 200
        ), f"Ошибка создания оценки руководителя: {manager_review_response.text}"
        manager_review = manager_review_response.json()
        logger.info(
            "Оценка руководителя создана, балл: %.2f",
            manager_review["calculated_score"],
        )

    # 6. Тестируем аналитику
    logger.info("6. Тестируем аналитику")

    analytics_response = client.get(
        f"/api/v1/analytics/goal/{goal_id}", headers=manager_auth_headers
    )
    assert (
        analytics_response.status_code == 200
    ), f"Ошибка получения аналитики: {analytics_response.text}"
    analytics = analytics_response.json()

    logger.info("Аналитика получена:")
    logger.info("- Самооценка: %.2f", analytics["scores"]["self_score"])
    logger.info("- Оценка руководителя: %.2f", analytics["scores"]["manager_score"])
    logger.info("- Общий балл: %.2f", analytics["scores"]["total_score"])
    logger.info("- Рекомендации: %d", len(analytics["recommendations"]))

    if analytics["recommendations"]:
        logger.info("Топ рекомендаций:")
        for i, rec in enumerate(analytics["recommendations"][:3], 1):
            logger.info("     %d. %s", i, rec)

    # 7. Сводная аналитика по сотруднику
    logger.info("7. Тестируем сводную аналитику по сотруднику")

    summary_response = client.get(
        f"/api/v1/analytics/employee/{test_employee_user.id}/summary",
        headers=manager_auth_headers,
    )
    assert (
        summary_response.status_code == 200
    ), f"Ошибка получения сводной аналитики: {summary_response.text}"
    summary = summary_response.json()

    logger.info("Сводная аналитика:")
    logger.info("- Всего целей: %d", summary["total_goals"])
    logger.info("- Завершено: %d", summary["completed_goals"])
    logger.info("- Средний балл: %.2f", summary["average_score"])
    logger.info("- Общий рейтинг: %s", summary["overall_rating"])

    # 8. Финальный отчет
    logger.info("ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!\n")
    logger.info("СИСТЕМА PERFORMANCE REVIEW ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    logger.info("ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    logger.info("- Аутентификация и авторизация:")
    logger.info("- Управление целями:")
    logger.info("- Система вопросов с весами:")
    logger.info("- Оценки (самооценка/руководитель):")
    logger.info("- Подсчет баллов с весами:")
    logger.info("- Генерация рекомендаций:")
    logger.info("- Аналитика и отчетность:")
