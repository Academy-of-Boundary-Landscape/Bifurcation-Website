# init_database.py
import asyncio
import logging
import os

from sqlalchemy import select

# 1. 导入数据库引擎和会话
from app.core.database import engine, AsyncSessionLocal
# 2. 导入 Base 类
from app.models.base import Base

# 3. 【关键】必须导入所有定义了的模型，否则 Base 找不到它们
from app.models.user import User, UserRole
from app.models.story_book import StoryBook
from app.models.story import StoryNode, NodeLike
from app.models.interaction import StoryComment, Notification
from app.utils.avatar import get_gravatar_url

from dotenv import load_dotenv
load_dotenv()
# 配置简单的日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_models():
    logger.info("开始初始化数据库...")
    async with engine.begin() as conn:
        # 先清除所有表（如果存在的话）
        await conn.run_sync(Base.metadata.drop_all)
        # 根据模型定义自动创建表
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表结构创建完成！")


async def maybe_create_prebound_admin_account():
    """可选：仅在显式提供 ADMIN_AUTH_SUBJECT 时预绑定管理员账号。"""
    default_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    default_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_auth_provider = os.getenv("ADMIN_AUTH_PROVIDER", "casdoor").strip() or "casdoor"
    admin_auth_subject = os.getenv("ADMIN_AUTH_SUBJECT", "").strip()
    admin_auth_user_id = os.getenv("ADMIN_AUTH_USER_ID", "").strip() or None
    normalized_email = default_email.strip().lower()
    normalized_username = default_username.strip()

    if not admin_auth_subject:
        logger.info(
            "未提供 ADMIN_AUTH_SUBJECT，跳过预创建管理员账号。"
            "当前推荐方式是让 Casdoor 管理员首次登录时，按 SSO admin claim 自动创建本地 admin。"
        )
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.auth_provider == admin_auth_provider,
                User.auth_subject == admin_auth_subject,
            )
        )
        existing = result.scalars().first()
        if existing:
            logger.info("管理员账户已存在：id=%s email=%s，跳过创建。", existing.id, existing.email)
            return

        username_result = await session.execute(select(User).where(User.username == normalized_username))
        username_owner = username_result.scalars().first()
        if username_owner:
            raise RuntimeError(
                f"ADMIN_USERNAME={normalized_username} 已被现有用户占用，请更换管理员用户名。"
            )

        admin = User(
            email=normalized_email,
            username=normalized_username,
            display_name=normalized_username,
            avatar=get_gravatar_url(normalized_email),
            hashed_password="",
            auth_provider=admin_auth_provider,
            auth_subject=admin_auth_subject,
            auth_user_id=admin_auth_user_id,
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(
            "预绑定管理员账户已创建：email=%s username=%s auth_provider=%s auth_subject=%s",
            default_email,
            default_username,
            admin_auth_provider,
            admin_auth_subject,
        )


async def main():
    await init_models()
    await maybe_create_prebound_admin_account()
    # 关闭引擎连接池
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
