# 容器启动时调用的安全 schema 同步脚本：只 create_all，不 drop。
# 与 init_database.py 区别：init_database.py 是首次部署用的破坏性重建，
# 本脚本是生产环境每次启动都跑的幂等迁移占位（未来接入 alembic 后可替换）。
import asyncio
import logging

from app.core.database import engine
from app.models.base import Base

# 必须导入所有模型，让 Base.metadata 注册表
from app.models.user import User  # noqa: F401
from app.models.story_book import StoryBook  # noqa: F401
from app.models.story import StoryNode, NodeLike  # noqa: F401
from app.models.interaction import StoryComment, Notification  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Running auto_migrate (create_all, non-destructive)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    logger.info("auto_migrate done.")


if __name__ == "__main__":
    asyncio.run(main())
