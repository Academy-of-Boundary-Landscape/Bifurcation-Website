# app/api/v1/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.story import StoryNode, NodeLike
from app.schemas import user as user_schema
from app.schemas import sso as sso_schema
from app.services.sso import build_sso_login_url, exchange_sso_code

router = APIRouter()

@router.get(
    "/sso/login-url",
    response_model=sso_schema.SSOLoginUrlResponse,
    summary="获取 Casdoor SSO 登录地址",
)
async def get_sso_login_url(
    redirect_to: str | None = Query(default="/books", description="登录成功后的站内跳转路径"),
):
    return build_sso_login_url(redirect_to)


@router.post(
    "/sso/exchange",
    response_model=sso_schema.SSOExchangeResponse,
    summary="Casdoor 授权码换取本站登录态",
)
async def exchange_sso_login(
    payload: sso_schema.SSOExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_sso_code(db, payload.code, payload.state)
    user: User = result["user"]
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )
    return sso_schema.SSOExchangeResponse(
        access_token=access_token,
        token_type="bearer",
        redirect_to=result["redirect_to"],
        is_new_user=result["is_new_user"],
    )

@router.get(
    "/me", 
    response_model=user_schema.UserProfileResponse, 
    summary="获取当前登录用户信息",
    operation_id="getMe",
)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. 获取基本用户信息
    user = current_user

    # 2. 统计数据

    # 用户发布过的节点总数
    nodes_count = (
        select(func.count(StoryNode.id))
        .where(StoryNode.author_id == user.id)
    )
    nodes_count = (await db.execute(nodes_count)).scalar() or 0
    # 用户收到的点赞总数
    likes_count = (
        select(func.count(NodeLike.user_id))
        .select_from(NodeLike)
        .join(StoryNode, NodeLike.node_id == StoryNode.id)
        .where(StoryNode.author_id == user.id)
    )
    likes_count = (await db.execute(likes_count)).scalar() or 0
    
    profile = user_schema.UserProfileResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        bio=user.bio,
        avatar=user.avatar,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        nodes_count=nodes_count,
        likes_count=likes_count,
    )   
    return profile

@router.patch(
    "/me", 
    response_model=user_schema.UserResponse, 
    summary="修改个人资料",
    operation_id="updateMe",
)
async def update_user_me(
    user_update: user_schema.UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # 使用 exclude_unset=True 防止把未传的字段改为空
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
