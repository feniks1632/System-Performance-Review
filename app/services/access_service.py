from sqlalchemy.orm import Session
from app.models.database import Goal, User


class AccessService:
    def __init__(self, db: Session):
        self.db = db

    def can_access_goal(self, goal_id: str, user_id: str) -> bool:
        """Проверяет, имеет ли пользователь доступ к цели"""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False

        # Владелец цели
        if goal.employee_id == user_id: # type: ignore
            return True

        # Менеджер
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_manager: # type: ignore
            return True

        # Респондент
        is_respondent = any(respondent.id == user_id for respondent in goal.respondents)
        if is_respondent:
            return True

        return False

    def is_goal_respondent(self, goal_id: str, user_id: str) -> bool:
        """Проверяет, является ли пользователь респондентом цели"""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False

        return any(respondent.id == user_id for respondent in goal.respondents)