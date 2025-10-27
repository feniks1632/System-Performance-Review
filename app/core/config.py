from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )  # type: ignore

    PROJECT_NAME: str = "Performance Review System"

    # Database - прямое присвоение значений по умолчанию
    DATABASE_URL: str = (
        "postgresql://postgres:password@localhost:5432/performance_review"
    )

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней

    # Email settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@company.com"
    SMTP_USE_TLS: bool = True
    BASE_URL: str = "http://localhost:8000"

    # Email templates
    COMPANY_NAME: str = "Performance Review System"


settings = Settings()
