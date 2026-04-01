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


async def create_admin_account():
    """创建一个默认管理员账号（绑定 SSO subject）。"""
    default_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    default_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_auth_provider = os.getenv("ADMIN_AUTH_PROVIDER", "casdoor").strip() or "casdoor"
    admin_auth_subject = os.getenv("ADMIN_AUTH_SUBJECT", "").strip()
    admin_auth_user_id = os.getenv("ADMIN_AUTH_USER_ID", "").strip() or None

    if not admin_auth_subject:
        raise RuntimeError(
            "缺少 ADMIN_AUTH_SUBJECT。当前初始化脚本会直接创建绑定 SSO 的管理员账号，"
            "请先在 .env 中配置管理员对应的 Casdoor subject。"
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == default_email))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"管理员账户已存在：{existing.email}，跳过创建。")
            return

        admin = User(
            email=default_email.strip().lower(),
            username=default_username.strip(),
            display_name=default_username.strip(),
            avatar=get_gravatar_url(default_email),
            hashed_password="",
            auth_provider=admin_auth_provider,
            auth_subject=admin_auth_subject,
            auth_user_id=admin_auth_user_id,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(
            "默认管理员账户已创建：email=%s username=%s auth_provider=%s auth_subject=%s",
            default_email,
            default_username,
            admin_auth_provider,
            admin_auth_subject,
        )


async def main():
    await init_models()
    await create_admin_account()
    # 关闭引擎连接池
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
