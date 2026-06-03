"""限流策略集中处：limiter 实例、key 函数、429 处理器、阈值常量。"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

# —— 阈值 ——
LIKE_LIMIT = "60/minute"      # 切赞按用户
COMMENT_LIMIT = "6/minute"    # 发评论按用户（防灌水）
SSO_LIMIT = "10/minute"       # 换登录态按 IP（未登录；装饰时须显式传 key_func=get_client_ip）


def get_client_ip(request: Request) -> str:
    """取真实客户端 IP。后端在 nginx 后面，必须读转发头，否则全是 127.0.0.1。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    client = request.client
    return client.host if client else "unknown"


def user_or_ip_key(request: Request) -> str:
    """默认 key：登录用户优先（deps 写入 request.state），否则回退到 IP。"""
    user_id = getattr(request.state, "rate_limit_user_id", None)
    if user_id is not None:
        return f"user:{user_id}"
    return get_client_ip(request)


limiter = Limiter(key_func=user_or_ip_key, enabled=settings.RATE_LIMIT_ENABLED)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """统一 429 响应：body 用全站 {"detail": ...} 形状，并注入 Retry-After 头。"""
    # 从触发的限速规则中取窗口大小（秒），作为 Retry-After 值。
    # exc.limit.limit 是 limits 库的 RateLimitItem，get_expiry() 返回窗口秒数。
    try:
        retry_after = str(exc.limit.limit.get_expiry())
    except Exception:
        retry_after = "60"
    return JSONResponse(
        status_code=429,
        content={"detail": "操作过于频繁，请稍后再试"},
        headers={"Retry-After": retry_after},
    )
