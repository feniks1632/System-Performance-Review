from app.models.database import User
from sqlalchemy.orm import Session
from typing import List, Optional


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_manager(self, user_id: str) -> Optional[User]:
        """Получить руководителя пользователя"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.manager_id:  # type: ignore
            return self.db.query(User).filter(User.id == user.manager_id).first()
        return None

    def get_user_subordinates(self, manager_id: str) -> List[User]:
        """Получить подчиненных руководителя"""
        return self.db.query(User).filter(User.manager_id == manager_id).all()

    def get_all_managers(self) -> List[User]:
        """Получить всех руководителей"""
        return self.db.query(User).filter(User.is_manager == True).all()

    def assign_manager(self, user_id: str, manager_id: str) -> bool:
        """Назначить руководителя сотруднику"""
        user = self.db.query(User).filter(User.id == user_id).first()
        manager = self.db.query(User).filter(User.id == manager_id).first()

        if not user or not manager or not manager.is_manager:  # type: ignore
            return False

        user.manager_id = manager_id  # type: ignore
        self.db.commit()
        return True
