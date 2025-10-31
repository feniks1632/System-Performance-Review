from datetime import timedelta

from starlette_admin.auth import AuthProvider, AdminConfig, AdminUser
from starlette_admin.exceptions import LoginFailed
from starlette.requests import Request
from starlette.responses import Response

from app.database.session import SessionLocal
from app.models.database import User
from app.core.security import verify_password, create_access_token, verify_token
from app.core.config import settings


class AdminAuthProvider(AuthProvider):
    """
    Провайдер аутентификации для админ-панели
    Доступ только для менеджеров (is_manager=True)
    """

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:

        # Создаем сессию БД
        db = SessionLocal()
        try:
            # Ищем пользователя по email
            user = db.query(User).filter(User.email == username).first()

            if not user or not verify_password(password, user.hashed_password):  # type: ignore
                raise LoginFailed("Неверное имя пользователя или пароль")

            if not user.is_active:  # type: ignore
                raise LoginFailed("Пользователь неактивен")

            # Проверяем права доступа - только менеджеры могут заходить в админку
            if not user.is_manager:  # type: ignore
                raise LoginFailed(
                    "Недостаточно прав для доступа в админ-панель. Требуются права менеджера."
                )

            # Создаем JWT токен
            access_token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = create_access_token(
                data={"sub": user.id}, expires_delta=access_token_expires
            )

            # Сохраняем токен в куки
            response.set_cookie(
                "admin_access_token",
                access_token,
                httponly=True,
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=not settings.DEBUG,
                samesite="lax",
            )

            # Также сохраняем ID пользователя для быстрого доступа
            response.set_cookie(
                "admin_user_id",
                str(user.id),
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                secure=not settings.DEBUG,
                samesite="lax",
            )

            return response

        finally:
            db.close()

    async def is_authenticated(self, request) -> bool:
        token = request.cookies.get("admin_access_token")
        user_id = request.cookies.get("admin_user_id")

        if not token or not user_id:
            return False

        try:
            # Проверяем токен
            token_user_id = verify_token(token)
            if not token_user_id or str(token_user_id) != user_id:
                return False

            # Проверяем что пользователь все еще существует и имеет права
            db = SessionLocal()
            try:
                user = (
                    db.query(User)
                    .filter(User.id == user_id, User.is_active == True)
                    .first()
                )

                if not user or not user.is_manager:  # type: ignore
                    return False

                # Сохраняем пользователя в state для использования в других методах
                request.state.user = {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_manager": user.is_manager,
                }

                return True
            finally:
                db.close()

        except Exception:
            return False

    def get_admin_config(self, request: Request) -> AdminConfig:
        user = getattr(request.state, "user", {})
        return AdminConfig(
            app_title="Панель управления Performance Review",
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user
        return AdminUser(
            username=user.get("email", "Пользователь"),
        )

    async def logout(self, request: Request, response: Response) -> Response:
        response.delete_cookie("admin_access_token")
        response.delete_cookie("admin_user_id")
        return response
