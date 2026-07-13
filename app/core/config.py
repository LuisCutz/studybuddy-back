import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-me-in-production-123456")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/studybuddy",
    )
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
