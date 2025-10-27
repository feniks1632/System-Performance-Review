from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.database import User
from app.api.endpoints.auth import get_current_user
from app.services.user_service import UserService
from app.models.schemas import UserResponse, SuccessResponse

router = APIRouter(tags=["users"])


@router.get(
    "/managers",
    response_model=List[UserResponse],
    summary="Получение списка руководителей",
    description="""
    Получение полного списка всех руководителей в системе.
    
    **Требования:**
    - Только пользователи с ролью руководителя (is_manager=True)
    - JWT токен с правами руководителя
    
    **Возвращает:**
    - Список объектов пользователей с ролью руководителя
    - Информация включает ID, email, полное имя и статус активности
    """,
)
async def get_all_managers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить всех руководителей (только для админов/руководителей)"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Only managers can view managers list"
        )

    user_service = UserService(db)
    managers = user_service.get_all_managers()
    return managers


@router.put(
    "/{user_id}/manager",
    response_model=SuccessResponse,
    summary="Назначение руководителя сотруднику",
    description="""
    Назначение руководителя для конкретного сотрудника.
    
    **Требования:**
    - Только пользователи с ролью руководителя (is_manager=True)
    - JWT токен с правами руководителя
    
    **Параметры:**
    - `user_id`: ID сотрудника, которому назначается руководитель
    - `manager_id`: ID пользователя с ролью руководителя
    
    **Возвращает:**
    - Статус операции и сообщение об успехе
    """,
)
async def assign_manager_to_user(
    user_id: str,
    manager_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Назначить руководителя сотруднику (только для руководителей)"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(status_code=403, detail="Only managers can assign managers")

    user_service = UserService(db)
    success = user_service.assign_manager(user_id, manager_id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign manager")

    return SuccessResponse(message="Manager assigned successfully")


@router.get(
    "/my-subordinates",
    response_model=List[UserResponse],
    summary="Получение списка подчиненных",
    description="""
    Получение списка сотрудников, которые находятся в подчинении у текущего руководителя.
    
    **Требования:**
    - Только пользователи с ролью руководителя (is_manager=True)
    - JWT токен с правами руководителя
    
    **Возвращает:**
    - Список объектов пользователей-подчиненных
    - Для каждого сотрудника отображается полная информация профиля
    - Включает сотрудников, у которых текущий пользователь назначен руководителем
    """,
)
async def get_my_subordinates(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить моих подчиненных (только для руководителей)"""
    if not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Only managers can view subordinates"
        )

    user_service = UserService(db)
    subordinates = user_service.get_user_subordinates(current_user.id)  # type: ignore
    return subordinates


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Получение профиля текущего пользователя",
    description="""
    Получение полной информации о профиле текущего аутентифицированного пользователя.
    
    **Требования:**
    - Любой аутентифицированный пользователь
    - Валидный JWT токен
    
    **Возвращает:**
    - Полную информацию о пользователе
    - Включая email, полное имя, роль руководителя, ID руководителя (если назначен)
    - Не включает хеш пароля
    """,
)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Получить профиль текущего пользователя"""
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получение информации о пользователе",
    description="""
    Получение информации о конкретном пользователе по ID.
    
    **Требования:**
    - Только руководители могут просматривать информацию о других пользователях
    - Обычные сотрудники могут просматривать только свой профиль
    
    **Параметры:**
    - `user_id`: ID запрашиваемого пользователя
    
    **Возвращает:**
    - Информацию о пользователе
    - 403 ошибку если нет прав доступа
    - 404 ошибку если пользователь не найден
    """,
)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить информацию о пользователе по ID"""
    if user_id != current_user.id and not current_user.is_manager:  # type: ignore
        raise HTTPException(
            status_code=403, detail="Not authorized to view this user's information"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
