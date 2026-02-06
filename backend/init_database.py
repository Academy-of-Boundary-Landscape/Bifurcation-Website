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
from app.core.security import get_password_hash

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
    """创建一个默认管理员账号（如已存在则跳过）。"""
    # 可以通过环境变量覆盖默认账号信息
    default_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    default_username = os.getenv("ADMIN_USERNAME", "admin")
    default_password = os.getenv("ADMIN_PASSWORD", "admin123")

    async with AsyncSessionLocal() as session:
        # 检查是否已存在该邮箱的用户
        result = await session.execute(select(User).where(User.email == default_email))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"管理员账户已存在：{existing.email}，跳过创建。")
            return

        admin = User(
            email=default_email,
            username=default_username,
            hashed_password=get_password_hash(default_password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(
            "默认管理员账户已创建：email=%s username=%s password=%s",
            default_email,
            default_username,
            default_password,
        )


async def main():
    await init_models()
    await create_admin_account()
    # 关闭引擎连接池
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())