# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.database.session import engine
from app.models.database import Base
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="""
    Performance Review System API
    
    ## Возможности
    
    * 🔐 **Аутентификация** - JWT токены
    * 🎯 **Управление целями** - создание, отслеживание целей сотрудников
    * 📊 **Performance Review** - самооценка, оценка руководителей, оценка респондентов
    * 📈 **Аналитика** - детальная аналитика по целям и сотрудникам
    * 🔔 **Уведомления** - in-app и email уведомления
    * 👥 **Роли** - сотрудники и руководители
    
    ## Авторизация
    
    Используйте Bearer токен в заголовке Authorization:
    `Authorization: Bearer {jwt_token}`
    """,
    contact={
        "name": "Development Team",
        "email": "dev@company.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

# Подключаем роутеры
from app.api.endpoints import auth, goals, reviews, analytics, notifications, users

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(
    notifications.router, prefix="/api/v1/notifications", tags=["notifications"]
)
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/")
async def root():
    return {"message": "Performance Review System API"}
