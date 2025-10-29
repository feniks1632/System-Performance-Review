import pytest
from app.models.database import QuestionTemplate
from app.database.session import SessionLocal

def test_question_template_creation():
    """Тест создания шаблона вопроса"""
    db = SessionLocal()
    try:
        # Создаем тестовый вопрос
        question = QuestionTemplate(
            question_text="Насколько сотрудник достиг запланированных результатов?",
            question_type="manager",
            section="performance",
            weight=1.5,
            max_score=10,
            order_index=1,
            trigger_words='["результат", "достижен", "план"]'
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        # Проверяем что вопрос создан
        assert question.id is not None
        assert question.question_text == "Насколько сотрудник достиг запланированных результатов?" # type: ignore
        assert question.question_type == "manager" # type: ignore
        assert question.weight == 1.5 # type: ignore
        assert question.is_active == True # type: ignore
        
    finally:
        db.rollback()  # Откатываем изменения
        db.close()
    

if __name__ == "__main__":
    test_question_template_creation()
    
