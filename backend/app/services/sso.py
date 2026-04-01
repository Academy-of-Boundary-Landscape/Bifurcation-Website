import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserRole

SSO_PROVIDER = "casdoor"
STATE_TOKEN_TYPE = "sso_state"


def _normalize_redirect_to(redirect_to: str | None) -> str:
    if not redirect_to:
        return "/books"
    if not redirect_to.startswith("/"):
        return "/books"
    if redirect_to.startswith("//"):
        return "/books"
    return redirect_to


def _create_state_token(redirect_to: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.SSO_STATE_EXPIRE_MINUTES)
    payload = {
        "type": STATE_TOKEN_TYPE,
        "redirect_to": redirect_to,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_state_token(state: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SSO state 无效或已过期") from exc

    if payload.get("type") != STATE_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SSO state 类型非法")
    return payload


def build_sso_login_url(redirect_to: str | None = None) -> dict[str, str]:
    if not settings.CASDOOR_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Casdoor CLIENT_ID 未配置")
    if not settings.CASDOOR_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Casdoor REDIRECT_URI 未配置")

    target = _normalize_redirect_to(redirect_to)
    state = _create_state_token(target)
    query = urlencode(
        {
            "client_id": settings.CASDOOR_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.CASDOOR_REDIRECT_URI,
            "scope": settings.CASDOOR_SCOPE,
            "state": state,
        }
    )
    return {
        "authorize_url": f"{settings.casdoor_authorize_url}?{query}",
        "state": state,
    }


async def _exchange_code_for_tokens(code: str) -> dict[str, Any]:
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.CASDOOR_CLIENT_ID,
        "client_secret": settings.CASDOOR_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.CASDOOR_REDIRECT_URI,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(settings.casdoor_token_url, data=payload)

    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Casdoor 授权码换取 token 失败")

    data = response.json()
    if "access_token" not in data and "id_token" not in data:
        raise HTTPException(status_code=400, detail="Casdoor token 响应缺少凭证")
    return data


async def _fetch_jwks() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(settings.casdoor_jwks_url)
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="无法获取 Casdoor JWKS")
    data = response.json()
    if not isinstance(data, dict) or "keys" not in data:
        raise HTTPException(status_code=400, detail="Casdoor JWKS 响应格式非法")
    return data


async def _decode_id_token(id_token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(id_token)
    kid = header.get("kid")
    jwks = await _fetch_jwks()
    key = None
    for item in jwks.get("keys", []):
        if item.get("kid") == kid:
            key = item
            break
    if key is None:
        raise HTTPException(status_code=400, detail="Casdoor JWKS 中找不到匹配的 kid")

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.casdoor_audience,
            issuer=settings.casdoor_issuer,
        )
    except JWTError as exc:
        raise HTTPException(status_code=400, detail="Casdoor ID Token 校验失败") from exc
    return claims


async def _fetch_userinfo(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            settings.casdoor_userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="无法获取 Casdoor 用户信息")
    data = response.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Casdoor 用户信息格式非法")
    return data


def _pick_claim(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def _flatten_claim_values(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return [part for part in parts if part]
    if isinstance(value, (list, tuple, set)):
        items: list[str] = []
        for item in value:
            items.extend(_flatten_claim_values(item))
        return items
    return [str(value).strip()]


def _resolve_initial_role(claims: dict[str, Any]) -> UserRole:
    admin_claim_keys = settings.sso_admin_claim_keys
    admin_match_values = settings.sso_admin_match_values
    if not admin_claim_keys or not admin_match_values:
        return UserRole.WRITER

    for claim_key in admin_claim_keys:
        for value in _flatten_claim_values(claims.get(claim_key)):
            if value.lower() in admin_match_values:
                return UserRole.ADMIN
    return UserRole.WRITER


def _build_username_seed(claims: dict[str, Any]) -> str:
    seed = (
        _pick_claim(claims, "preferred_username", "username", "name")
        or (_pick_claim(claims, "email") or "writer").split("@")[0]
    )
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", str(seed)).strip("_").lower()
    if not normalized:
        normalized = "writer"
    if len(normalized) < 3:
        normalized = f"{normalized}_user"
    return normalized[:50]


async def _generate_available_username(db: AsyncSession, claims: dict[str, Any]) -> str:
    base = _build_username_seed(claims)
    candidate = base
    suffix = 2
    while True:
        existing = (await db.execute(select(User).where(User.username == candidate))).scalars().first()
        if not existing:
            return candidate
        suffix_text = f"_{suffix}"
        candidate = f"{base[: max(1, 50 - len(suffix_text))]}{suffix_text}"
        suffix += 1


def _sync_user_fields(user: User, claims: dict[str, Any]) -> None:
    email = _pick_claim(claims, "email")
    display_name = _pick_claim(claims, "name", "displayName")
    avatar = _pick_claim(claims, "picture", "avatar")
    external_user_id = _pick_claim(claims, "id", "user_id")
    email_verified = _pick_claim(claims, "email_verified", "emailVerified")

    if email:
        user.email = str(email).strip().lower()
    if display_name:
        user.display_name = str(display_name).strip()[:60]
    if avatar:
        user.avatar = str(avatar).strip()[:255]
    if external_user_id:
        user.auth_user_id = str(external_user_id)
    if email_verified is not None:
        user.is_verified = bool(email_verified)
    user.auth_provider = SSO_PROVIDER
    user.auth_subject = str(claims["sub"])
    now = datetime.now(timezone.utc)
    user.auth_last_sync_at = now
    user.last_login_at = now


async def _find_or_create_local_user(db: AsyncSession, claims: dict[str, Any]) -> tuple[User, bool]:
    subject = str(claims["sub"])
    user = (
        await db.execute(
            select(User).where(
                User.auth_provider == SSO_PROVIDER,
                User.auth_subject == subject,
            )
        )
    ).scalars().first()
    is_new_user = False

    if user is None and settings.SSO_AUTO_LINK_BY_EMAIL:
        email = _pick_claim(claims, "email")
        email_verified = bool(_pick_claim(claims, "email_verified", "emailVerified"))
        if email and email_verified:
            matched_users = (
                await db.execute(select(User).where(User.email == str(email).strip().lower()))
            ).scalars().all()
            if len(matched_users) > 1:
                raise HTTPException(status_code=409, detail="该邮箱对应多个本地账号，不能自动绑定 SSO")
            user = matched_users[0] if matched_users else None
            if user and user.role == UserRole.ADMIN and user.auth_subject != subject:
                raise HTTPException(status_code=409, detail="管理员账号不能自动通过邮箱绑定 SSO")
            if user and user.auth_provider and user.auth_subject and user.auth_subject != subject:
                raise HTTPException(status_code=409, detail="该邮箱已绑定其他 SSO 身份")

    if user is None:
        username = await _generate_available_username(db, claims)
        user = User(
            email=str((_pick_claim(claims, "email") or f"{username}@local.invalid")).strip().lower(),
            username=username,
            role=_resolve_initial_role(claims),
            is_active=True,
            is_verified=bool(_pick_claim(claims, "email_verified", "emailVerified")),
            hashed_password="",
        )
        is_new_user = True

    _sync_user_fields(user, claims)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, is_new_user


async def _resolve_claims(token_data: dict[str, Any]) -> dict[str, Any]:
    if token_data.get("id_token"):
        claims = await _decode_id_token(token_data["id_token"])
    elif token_data.get("access_token"):
        claims = await _fetch_userinfo(token_data["access_token"])
    else:
        raise HTTPException(status_code=400, detail="Casdoor 响应中缺少可用身份凭证")

    if not claims.get("sub"):
        raise HTTPException(status_code=400, detail="Casdoor 用户信息缺少 sub")
    return claims


async def exchange_sso_code(db: AsyncSession, code: str, state: str) -> dict[str, Any]:
    state_payload = _decode_state_token(state)
    token_data = await _exchange_code_for_tokens(code)
    claims = await _resolve_claims(token_data)
    user, is_new_user = await _find_or_create_local_user(db, claims)
    return {
        "user": user,
        "is_new_user": is_new_user,
        "redirect_to": _normalize_redirect_to(state_payload.get("redirect_to")),
    }
