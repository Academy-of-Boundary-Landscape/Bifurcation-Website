# app/core/config.py
from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    PROJECT_NAME: str = "Tree Story Project"
    API_V1_STR: str = "/api/v1"
    
    # 格式: mysql+aiomysql://user:password@host:port/db_name
    DATABASE_URL: str =  os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/bifurcation_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "GANGWAY")  # 请在生产环境中使用更安全的密钥
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天过期

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    

    class Config:
        env_file = ".env"

settings = Settings()