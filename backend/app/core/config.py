import os
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic.config import ConfigDict
from pydantic_settings import BaseSettings

# config.py 在 backend/app/core/，往上三层到 backend/
_BACKEND_DIR = Path(__file__).parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


def _resolve_database_url() -> str:
    app_env = os.getenv("APP_ENV", "dev").lower()
    if app_env == "dev":
        return os.getenv("DEV_DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("生产环境必须在 .env 中设置 DATABASE_URL")
    return url


def _resolve_cors_origins() -> list[str]:
    raw_value = os.getenv("CORS_ORIGINS", "").strip()
    if raw_value:
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    return [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Tree Story Project"
    API_V1_STR: str = "/api/v1"

    # 开发环境 (APP_ENV=dev): sqlite+aiosqlite:///./dev.db
    # 生产环境 (APP_ENV=prod): postgresql+asyncpg://user:password@host:port/db_name
    DATABASE_URL: str = _resolve_database_url()

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天过期
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes", "on"}

    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")

    # Casdoor / SSO 配置
    CASDOOR_BASE_URL: str = os.getenv("CASDOOR_BASE_URL", "")
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
    SSO_ADMIN_CLAIM_KEYS: str = os.getenv("SSO_ADMIN_CLAIM_KEYS", "roles,role")
    SSO_ADMIN_MATCH_VALUES: str = os.getenv("SSO_ADMIN_MATCH_VALUES", "admin,administrator")

    # CORS 配置
    CORS_ORIGINS: list[str] = _resolve_cors_origins()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                import json

                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw_value.split(",") if item.strip()]
        return _resolve_cors_origins()

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
        base_url = self.CASDOOR_BASE_URL.rstrip("/")
        if self.CASDOOR_JWKS_URL:
            return self.CASDOOR_JWKS_URL
        if self.CASDOOR_APPLICATION_NAME:
            return f"{base_url}/.well-known/{self.CASDOOR_APPLICATION_NAME}/jwks"
        return f"{base_url}/.well-known/jwks"

    @property
    def casdoor_issuer(self) -> str:
        base_url = self.CASDOOR_BASE_URL.rstrip("/")
        if self.CASDOOR_ISSUER:
            return self.CASDOOR_ISSUER
        if self.CASDOOR_APPLICATION_NAME:
            return f"{base_url}/.well-known/{self.CASDOOR_APPLICATION_NAME}"
        return base_url

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

# 启动时强制检查生产环境必填项，防止使用空/默认值上线
if os.getenv("APP_ENV", "dev").lower() == "prod":
    _missing = [name for name, val in [
        ("SECRET_KEY", settings.SECRET_KEY),
        ("CASDOOR_CLIENT_ID", settings.CASDOOR_CLIENT_ID),
        ("CASDOOR_CLIENT_SECRET", settings.CASDOOR_CLIENT_SECRET),
        ("CASDOOR_REDIRECT_URI", settings.CASDOOR_REDIRECT_URI),
    ] if not val]
    if _missing:
        raise RuntimeError(f"生产环境缺少必填配置项: {', '.join(_missing)}")
