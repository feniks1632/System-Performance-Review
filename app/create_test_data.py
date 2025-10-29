"""
Скрипт для создания тестовых данных системы Performance Review
"""
import sys
import os
from datetime import datetime, timedelta

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.database import User, QuestionTemplate, Goal
from app.core.security import get_password_hash
from app.core.logger import logger

def create_test_data():
    """Создание тестовых данных"""
    db = SessionLocal()
    
    try:
        logger.info("Создание тестовых данных...")
        
        # 1. Создаем тестовых пользователей
        print("Создаем пользователей...")
        
        manager1 = User(
            email="manager1@company.com",
            full_name="Иван Петров (Руководитель)",
            hashed_password=get_password_hash("password123"),
            is_manager=True
        )
        
        manager2 = User(
            email="manager2@company.com", 
            full_name="Мария Сидорова (Руководитель)",
            hashed_password=get_password_hash("password123"),
            is_manager=True
        )
        
        employee1 = User(
            email="employee1@company.com",
            full_name="Алексей Козлов (Сотрудник)",
            hashed_password=get_password_hash("password123"), 
            is_manager=False,
            manager_id=None  # Установим позже
        )
        
        employee2 = User(
            email="employee2@company.com",
            full_name="Елена Новикова (Сотрудник)", 
            hashed_password=get_password_hash("password123"),
            is_manager=False,
            manager_id=None
        )
        
        respondent1 = User(
            email="respondent1@company.com",
            full_name="Дмитрий Волков (Коллега)",
            hashed_password=get_password_hash("password123"),
            is_manager=False
        )
        
        db.add_all([manager1, manager2, employee1, employee2, respondent1])
        db.commit()
        
        # Обновляем объекты после коммита
        db.refresh(manager1)
        db.refresh(manager2)
        db.refresh(employee1)
        db.refresh(employee2)
        
        # Устанавливаем руководителей
        employee1.manager_id = manager1.id
        employee2.manager_id = manager2.id
        db.commit()
        
        print(f"Создано пользователей: 2 руководителя, 2 сотрудника, 1 респондент")

        # 2. Создаем тестовые цели
        print("Создаем тестовые цели...")
        
        future_date = datetime.now() + timedelta(days=90)
        
        goal1 = Goal(
            title="Разработка нового функционала системы",
            description="Реализация модуля аналитики и отчетности в Performance Review System",
            expected_result="Запущенный в продакшен модуль с полным покрытием требований",
            deadline=future_date,
            task_link="https://jira.company.com/TASK-123",
            employee_id=employee1.id,
            status="active"
        )
        
        goal2 = Goal(
            title="Оптимизация процессов код-ревью", 
            description="Внедрение новых практик код-ревью и улучшение качества кода",
            expected_result="Снижение количества багов на 20% и ускорение процесса ревью на 30%",
            deadline=future_date,
            task_link="https://jira.company.com/TASK-124", 
            employee_id=employee2.id,
            status="active"
        )
        
        db.add_all([goal1, goal2])
        db.commit()
        
        # Добавляем респондентов к целям (после создания целей)
        goal1.respondents.append(respondent1)
        goal2.respondents.append(respondent1)
        db.commit()
        
        (f"Создано тестовых целей: 2")

        logger.info("\nТестовые данные успешно созданы!")
        logger.info("\nСозданные учетные записи:")
        logger.info("Руководители:")
        logger.info(f"- manager1@company.com / password123 (Иван Петров)")
        logger.info(f"- manager2@company.com / password123 (Мария Сидорова)")
        logger.info("Сотрудники:")
        logger.info(f"- employee1@company.com / password123 (Алексей Козлов)")
        logger.info(f"- employee2@company.com / password123 (Елена Новикова)") 
        logger.info("Респондент:")
        logger.info(f"- respondent1@company.com / password123 (Дмитрий Волков)")
        logger.info(f"\nSwagger UI: http://localhost:8000/docs")
        
    except Exception as e:
        logger.info(f"Ошибка при создании тестовых данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()