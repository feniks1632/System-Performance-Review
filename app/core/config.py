from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Игнорировать лишние переменные в .env
    )  # type: ignore

    # Project
    PROJECT_NAME: str = "Performance Review System"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://review_user:review_password@localhost:5432/performance_review",
        description="PostgreSQL connection string",
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        min_length=32,
        description="JWT secret key - минимум 32 символа",
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=10080)  # 7 дней

    # Email settings
    SMTP_SERVER: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="noreply@company.com")
    SMTP_USE_TLS: bool = Field(default=True)

    # Application
    BASE_URL: str = Field(default="http://localhost:8000")
    COMPANY_NAME: str = Field(default="Performance Review System")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    def validate_settings(self):
        """Валидация критически важных настроек"""
        if not self.SMTP_USERNAME or not self.SMTP_PASSWORD:
            raise ValueError(
                "SMTP_USERNAME and SMTP_PASSWORD must be set for email service"
            )

        if self.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("Change SECRET_KEY in production environment!")


settings = Settings()

# Автоматическая валидация при импорте
try:
    settings.validate_settings()
    print("Конфигурация загружена успешно!")
except ValueError as e:
    print(f"Внимание: {e}")
