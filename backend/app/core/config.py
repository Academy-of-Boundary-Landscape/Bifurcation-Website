# app/core/config.py
from pydantic_settings import BaseSettings
import os


def _resolve_database_url() -> str:
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env == "dev":
        return os.getenv("DEV_DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    return os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/tree_story_db")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tree Story Project"
    API_V1_STR: str = "/api/v1"
    
    # 开发环境 (APP_ENV=dev): sqlite+aiosqlite:///./dev.db
    # 生产环境 (APP_ENV=prod): postgresql+asyncpg://user:password@host:port/db_name
    DATABASE_URL: str = _resolve_database_url()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "GANGWAY")  # 请在生产环境中使用更安全的密钥
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天过期

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"

settings = Settings()