import os
from typing import Optional

from pydantic_settings import BaseSettings


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

    # Casdoor / SSO 配置
    CASDOOR_BASE_URL: str = os.getenv("CASDOOR_BASE_URL", "https://auth.secret-sealing.club")
    CASDOOR_CLIENT_ID: str = os.getenv("CASDOOR_CLIENT_ID", "")
    CASDOOR_CLIENT_SECRET: str = os.getenv("CASDOOR_CLIENT_SECRET", "")
    CASDOOR_ORGANIZATION_NAME: str = os.getenv("CASDOOR_ORGANIZATION_NAME", "")
    CASDOOR_APPLICATION_NAME: str = os.getenv("CASDOOR_APPLICATION_NAME", "")
    CASDOOR_REDIRECT_URI: str = os.getenv("CASDOOR_REDIRECT_URI", "")
    CASDOOR_SCOPE: str = os.getenv("CASDOOR_SCOPE", "openid profile email")
    CASDOOR_AUTHORIZE_URL: Optional[str] = os.getenv("CASDOOR_AUTHORIZE_URL") or None
    CASDOOR_TOKEN_URL: Optional[str] = os.getenv("CASDOOR_TOKEN_URL") or None
    CASDOOR_USERINFO_URL: Optional[str] = os.getenv("CASDOOR_USERINFO_URL") or None
    CASDOOR_JWKS_URL: Optional[str] = os.getenv("CASDOOR_JWKS_URL") or None
    CASDOOR_ISSUER: Optional[str] = os.getenv("CASDOOR_ISSUER") or None
    CASDOOR_AUDIENCE: Optional[str] = os.getenv("CASDOOR_AUDIENCE") or None
    SSO_STATE_EXPIRE_MINUTES: int = int(os.getenv("SSO_STATE_EXPIRE_MINUTES", "10"))
    SSO_AUTO_LINK_BY_EMAIL: bool = os.getenv("SSO_AUTO_LINK_BY_EMAIL", "true").lower() in {"1", "true", "yes", "on"}
    SSO_ADMIN_CLAIM_KEYS: str = os.getenv("SSO_ADMIN_CLAIM_KEYS", "roles,role,groups")
    SSO_ADMIN_MATCH_VALUES: str = os.getenv("SSO_ADMIN_MATCH_VALUES", "admin,administrator")

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"

    @property
    def casdoor_authorize_url(self) -> str:
        return self.CASDOOR_AUTHORIZE_URL or f"{self.CASDOOR_BASE_URL.rstrip('/')}/login/oauth/authorize"

    @property
    def casdoor_token_url(self) -> str:
        return self.CASDOOR_TOKEN_URL or f"{self.CASDOOR_BASE_URL.rstrip('/')}/api/login/oauth/access_token"

    @property
    def casdoor_userinfo_url(self) -> str:
        return self.CASDOOR_USERINFO_URL or f"{self.CASDOOR_BASE_URL.rstrip('/')}/api/userinfo"

    @property
    def casdoor_jwks_url(self) -> str:
        return self.CASDOOR_JWKS_URL or f"{self.CASDOOR_BASE_URL.rstrip('/')}/.well-known/jwks.json"

    @property
    def casdoor_issuer(self) -> str:
        return self.CASDOOR_ISSUER or self.CASDOOR_BASE_URL.rstrip("/")

    @property
    def casdoor_audience(self) -> str:
        return self.CASDOOR_AUDIENCE or self.CASDOOR_CLIENT_ID

    @property
    def sso_admin_claim_keys(self) -> list[str]:
        return [item.strip() for item in self.SSO_ADMIN_CLAIM_KEYS.split(",") if item.strip()]

    @property
    def sso_admin_match_values(self) -> set[str]:
        return {item.strip().lower() for item in self.SSO_ADMIN_MATCH_VALUES.split(",") if item.strip()}

settings = Settings()
