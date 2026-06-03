from __future__ import annotations

import sys
import unittest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 测试默认关闭限流：slowapi enabled=False 时直接短路，既不误伤既有用例，
# 也不在进程内跨用例累积内存计数。专用测试 test_rate_limit.py 会临时开启。
from app.core.rate_limit import limiter as _limiter
_limiter.enabled = False


class BackendAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    pass


class _ScalarsResult:
    def __init__(self, *, first: Any = None, all_items: list[Any] | None = None):
        self._first = first
        self._all_items = all_items or []

    def first(self) -> Any:
        return self._first

    def all(self) -> list[Any]:
        return list(self._all_items)


class ExecuteResult:
    def __init__(self, *, first: Any = None, all_items: list[Any] | None = None, scalar: Any = None):
        self._scalars = _ScalarsResult(first=first, all_items=all_items)
        self._scalar = scalar

    def scalars(self) -> _ScalarsResult:
        return self._scalars

    def scalar(self) -> Any:
        return self._scalar

    def scalar_one_or_none(self) -> Any:
        return self._scalar


class SyncSessionAdapter:
    def __init__(self, session: Session):
        self._session = session

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.get(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.execute(*args, **kwargs)

    def add(self, instance: Any) -> None:
        self._session.add(instance)

    async def flush(self) -> None:
        self._session.flush()

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()

    async def refresh(self, instance: Any) -> None:
        self._session.refresh(instance)

    async def delete(self, instance: Any) -> None:
        self._session.delete(instance)

    async def close(self) -> None:
        self._session.close()


class SQLiteIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        loop = asyncio.get_running_loop()
        loop.set_debug(False)
        loop.slow_callback_duration = 10

        from app.core.database import get_db
        from app.models.base import Base
        import app.models.user  # noqa: F401
        import app.models.story_book  # noqa: F401
        import app.models.story  # noqa: F401
        import app.models.interaction  # noqa: F401
        from main import app

        self._app = app
        self._get_db = get_db
        self._tmpdir = TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "integration.db"
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        Base.metadata.create_all(self.engine)

        async def override_get_db():
            session = self.SessionLocal()
            adapter = SyncSessionAdapter(session)
            try:
                yield adapter
            finally:
                await adapter.close()

        self._app.dependency_overrides[self._get_db] = override_get_db
        self.client = AsyncClient(
            transport=ASGITransport(app=self._app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        self._app.dependency_overrides.clear()
        self.engine.dispose()
        self._tmpdir.cleanup()

    def db_session(self) -> Session:
        return self.SessionLocal()
