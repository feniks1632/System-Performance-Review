from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.session import get_db
from app.models.schemas import UserCreate, UserResponse, Token, UserLogin
from app.models.database import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
)
from app.core.config import settings


router = APIRouter(tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Зависимость для получения текущего пользователя из JWT токена"""
    user_id = verify_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    summary="Регистрация пользователя",
    description="Создание нового пользователя в системе. Для сотрудников is_manager=False, для руководителей - True.",
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем, нет ли уже пользователя с таким email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # ПРОВЕРЯЕМ РУКОВОДИТЕЛЯ (если указан)
    if user_data.manager_id:
        manager = (
            db.query(User)
            .filter(User.id == user_data.manager_id, User.is_manager == True)
            .first()
        )
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manager not found or is not a manager",
            )

    # Создаем пользователя (ТОЛЬКО те поля, которые есть в UserCreate)
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        is_manager=user_data.is_manager,
        hashed_password=hashed_password,
        manager_id=user_data.manager_id,  # СОХРАНЯЕМ РУКОВОДИТЕЛЯ
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Аутентификация",
    description="Вход в систему. Возвращает JWT токен для доступа к защищенным endpoints.",
)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Аутентификация пользователя"""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Профиль текущего пользователя",
    description="Получение информации о текущем аутентифицированном пользователе.",
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user
