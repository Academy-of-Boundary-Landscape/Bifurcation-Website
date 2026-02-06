# app/api/v1/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, select
from fastapi.security import OAuth2PasswordRequestForm
from random import randint
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.story import StoryNode, NodeLike
from app.schemas import user as user_schema
from app.schemas import token as token_schema
from app.schemas.story import MessageResponse # 引入通用的消息响应模型
from app.schemas import common as common_schema
from app.utils import get_gravatar_url, send_email_code
from app.models.auth import EmailVerificationCode, VerificationPurpose
router = APIRouter()

# ==========================================
# ✉️ 验证模块
# ==========================================

@router.post(
    "/send-code-for-activation", 
    response_model=MessageResponse, # 显式定义返回模型
    summary="发送邮箱验证码",
    operation_id="sendVerificationCode",
    responses={
        200: {"description": "验证码发送成功"},
        400: {"model": MessageResponse, "description": "邮箱已注册并激活"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    }
)
async def send_verification_code(
    email_data: user_schema.UserEmail, 
    db: AsyncSession = Depends(get_db)
):
    """
    把发送邮件的功能单独拆出来，方便前端在注册前调用。
    在写完邮件逻辑之前可以是一个mock的实现，打印到控制台。
    """
    # 检查邮箱是否已被注册且已验证
    result = await db.execute(select(User).where(User.email == email_data.email))
    user = result.scalars().first()
    if user and user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已注册并激活，请直接登录",
        )
    # 检查是否存在一分钟内发送过的验证码
    recent_code_stmt = (
        select(func.count())
        .where(EmailVerificationCode.email == email_data.email)
        .where(EmailVerificationCode.created_at >= datetime.utcnow() - timedelta(minutes=1))
    )
    recent_code_count = (await db.execute(recent_code_stmt)).scalar() or 0
    if recent_code_count > 0:
        raise HTTPException(
            status_code=400,
            detail="请勿频繁发送验证码，1分钟内只能发送一次",
        )
    # 在数据库创建一个新的验证码
    verification_code = EmailVerificationCode(
        email=email_data.email,
        purpose=VerificationPurpose.REGISTER,
        code=str(randint(100000, 999999)),
        expires_at=datetime.utcnow() + timedelta(minutes=10)  # 验证码有效期10分钟
    )
    db.add(verification_code)
    await db.commit()
    
    # 发送一个6位的随机整数验证码
    await send_email_code(email_data.email, verification_code.code)
    
    return {"detail": "验证码已发送 (测试环境请查看控制台输出或直接使用 114514)"}


@router.post(
    "/verify-email-for-activation", 
    response_model=MessageResponse, 
    summary="验证邮箱验证码, 用于激活账号",
)
async def verify_email(
    verify_in: user_schema.EmailVerify,
    db: AsyncSession = Depends(get_db)
):
    code = verify_in.code
    email = verify_in.email

    # 在数据库中查找最新的未使用且未过期的验证码
    stmt = (
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == email)
        .where(EmailVerificationCode.purpose == VerificationPurpose.REGISTER)
        .where(EmailVerificationCode.is_used == False)
        .where(EmailVerificationCode.expires_at > datetime.utcnow())
        .order_by(EmailVerificationCode.created_at.desc())
    )
    result = await db.execute(stmt)
    verification_code: Optional[EmailVerificationCode] = result.scalars().first()
    if not verification_code:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    # 检测验证码是否匹配
    if not security.verify_email_code(code, verification_code.code):
        raise HTTPException(status_code=400, detail="验证码错误")
    # 标记验证码为已使用
    verification_code.is_used = True
    db.add(verification_code)
    # 激活对应的用户账号
    user_stmt = select(User).where(User.email == email)
    user_result = await db.execute(user_stmt)
    user: Optional[User] = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_verified = True
    db.add(user)

    await db.commit()
    
    return {"detail": "邮箱验证成功，账号已激活"}


# ==========================================
# 👤 用户管理模块
# ==========================================

@router.post(
    "/register", 
    response_model=user_schema.UserCreateResponse, 
    summary="用户注册",
)
async def register(
    user_in: user_schema.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # 检查邮箱重复
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="该邮箱已被使用")
    
    # 检查用户名重复 (Schemathesis 可能会尝试重复的用户名)
    result_un = await db.execute(select(User).where(User.username == user_in.username))
    if result_un.scalars().first():
        raise HTTPException(status_code=400, detail="该用户名已被占用")

    # 检查密码安全性
    if not security.is_password_strong(user_in.password):
        raise HTTPException(status_code=400, detail="密码强度不足")
    user = User(
        email=user_in.email.strip().lower(),
        username=user_in.username.strip(),
        hashed_password=security.get_password_hash(user_in.password),
        role=UserRole.WRITER,
        is_active=True,
        is_verified=False,
        avatar=get_gravatar_url(user_in.email.strip().lower())
    )
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="数据库内部错误，请稍后重试")



@router.post(
    "/login",
    response_model=token_schema.Token,
    summary="登录获取Token（邮箱或用户名）",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Swagger/OAuth2 Password Flow 兼容：
    - form_data.username：可以填邮箱或用户名
    - form_data.password：密码
    """

    identifier_raw = (form_data.username or "").strip()
    password = form_data.password or ""

    if not identifier_raw or not password:
        # 也可以交给 422，但这里手动给 400 更友好
        raise HTTPException(status_code=400, detail="请输入用户名/邮箱和密码")

    # email 统一 lowercase；用户名保持原样（是否大小写敏感取决于你业务）
    identifier_email = identifier_raw.lower()

    stmt = select(User).where(
        or_(
            User.email == identifier_email,
            User.username == identifier_raw,
        )
    )
    user = (await db.execute(stmt)).scalars().first()

    # 统一 401：避免泄露“用户是否存在”
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱/用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 账号状态检查（按你当前语义：is_active=False 或 role=banned 都算封禁）
    if user.role == UserRole.BANNED or not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被封禁")

    if not user.is_verified:
        raise HTTPException(status_code=400, detail="账号未激活，请先验证邮箱以激活账号")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user.id),   # ✅ sub 建议用 str
        expires_delta=access_token_expires,
    )

    return token_schema.Token(access_token=access_token, token_type="bearer")

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
    nodes_count = select(
        func.count(StoryNode.id)
        .where(StoryNode.author_id == user.id)
    )
    nodes_count = (await db.execute(nodes_count)).scalar() or 0
    # 用户收到的点赞总数
    likes_count = select(
        func.count(NodeLike.user_id)
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
        is_verified=user.is_verified,
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
    responses={
        200: {"description": "更新成功"},
        400: {"model": MessageResponse, "description": "用户被封禁"},
        401: {"model": MessageResponse, "description": "未认证"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    }
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

# ==========================================
# 🔐 安全模块
# ==========================================

@router.post(
    "/send-code-for-password-reset", 
    response_model=MessageResponse, 
    summary="验证邮箱并发送重置密码验证码",
)
async def send_verification_code_for_password_reset(
    email_data: user_schema.EmailVerify, 
    db: AsyncSession = Depends(get_db)
):
    # 检查邮箱是否已被注册且已验证
    result = await db.execute(select(User).where(User.email == email_data.email))
    user = result.scalars().first()
    if not user or not user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="该邮箱未注册或未激活",
        )
    # 在数据库创建一个新的验证码
    verification_code = EmailVerificationCode(
        email=email_data.email,
        purpose=VerificationPurpose.PASSWORD_RESET,
        code=str(randint(100000, 999999)),
        expires_at=datetime.utcnow() + timedelta(minutes=10)  # 验证码有效期10分钟
    )
    db.add(verification_code)
    await db.commit()
    
    # 发送一个6位的随机整数验证码
    await send_email_code(email_data.email, verification_code.code)
    
    return {"detail": "验证码已发送 (测试环境请查看控制台输出或直接使用 114514)"}
@router.post(
    "/reset-password", 
    response_model=MessageResponse, 
    summary="重置密码",
)
async def reset_password(
    reset_data: user_schema.PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    if not security.is_password_strong(reset_data.new_password):
        raise HTTPException(status_code=400, detail="密码强度不足")
    # 检查是否存在一分钟内发送过的验证码
    recent_code_stmt = (
        select(func.count())
        .where(EmailVerificationCode.email == reset_data.email)
        .where(EmailVerificationCode.created_at >= datetime.utcnow() - timedelta(minutes=1))
    )
    recent_code_count = (await db.execute(recent_code_stmt)).scalar() or 0
    if recent_code_count > 0:
        raise HTTPException(
            status_code=400,
            detail="请勿频繁发送验证码，1分钟内只能发送一次",
        )
    # 验证验证码
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == reset_data.email,
            EmailVerificationCode.purpose == VerificationPurpose.PASSWORD_RESET,
            EmailVerificationCode.code == reset_data.code,
            EmailVerificationCode.expires_at > datetime.utcnow()
        )
    )
    verification_code = result.scalars().first()
    if not verification_code:
        raise HTTPException(
            status_code=400,
            detail="验证码无效或已过期",
        )
    
    # 更新用户密码
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="用户不存在",
        )
    user.hashed_password = security.get_password_hash(reset_data.new_password)
    db.add(user)
    await db.commit()
    
    return {"detail": "密码重置成功"}