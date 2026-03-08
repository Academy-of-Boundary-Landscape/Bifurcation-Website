import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select


DB_FILE = Path(__file__).resolve().parent.parent / "test_0227.db"
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("DEV_DATABASE_URL", f"sqlite+aiosqlite:///{DB_FILE}")

from app.main import app
from app.core.database import AsyncSessionLocal, engine
from app.models.base import Base
from app.models.auth import EmailVerificationCode, VerificationPurpose
from app.models.story import NodeStatus, NodeVisibility, NodeZone, StoryNode
from app.models.story_book import BookPhase, StoryBook
from app.models.user import User, UserRole
from app.core.security import get_password_hash


SEED = {"book_id": None, "node_id": None}


def run(coro):
    return asyncio.run(coro)


async def _prepare_db() -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        admin = User(
            email="admin_test_0227@example.com",
            username="admin_test_0227",
            hashed_password=get_password_hash("Admin123456"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.flush()

        book = StoryBook(
            title="测试活动-0227",
            description="用于核心功能测试",
            phase=BookPhase.WRITING,
            allow_new_nodes=True,
        )
        session.add(book)
        await session.flush()

        now = datetime.now(timezone.utc)
        root_node = StoryNode(
            book_id=book.id,
            parent_id=None,
            root_id=0,
            author_id=admin.id,
            title="测试根节点",
            content="这是用于自动化测试的已发布根节点内容。",
            summary="测试摘要",
            branch_name="主线",
            zone=NodeZone.SHORT,
            word_count=20,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
            published_at=now,
            last_activity_at=now,
        )
        session.add(root_node)
        await session.flush()

        root_node.root_id = root_node.id

        await session.commit()

        SEED["book_id"] = book.id
        SEED["node_id"] = root_node.id


async def _cleanup_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if DB_FILE.exists():
        DB_FILE.unlink()


async def _latest_register_code(email: str) -> str:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(EmailVerificationCode)
            .where(EmailVerificationCode.email == email)
            .where(EmailVerificationCode.purpose == VerificationPurpose.REGISTER)
            .order_by(EmailVerificationCode.created_at.desc())
        )
        code_obj = (await session.execute(stmt)).scalars().first()
        assert code_obj is not None, "未找到激活验证码"
        return code_obj.code


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    run(_prepare_db())
    yield
    run(_cleanup_db())


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_01_public_core_endpoints(client: TestClient):
    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200

    books_resp = client.get("/api/v1/story/books")
    assert books_resp.status_code == 200
    books = books_resp.json()
    assert isinstance(books, list)
    assert any(item["id"] == SEED["book_id"] for item in books)

    tree_resp = client.get(f"/api/v1/story/tree?book_id={SEED['book_id']}")
    assert tree_resp.status_code == 200
    tree = tree_resp.json()
    assert isinstance(tree, list)
    assert any(item["id"] == SEED["node_id"] for item in tree)

    feed_resp = client.get("/api/v1/discovery/feed?limit=10")
    assert feed_resp.status_code == 200
    feed = feed_resp.json()
    assert isinstance(feed, list)
    assert any(item["id"] == SEED["node_id"] for item in feed)

    search_resp = client.get("/api/v1/discovery/search?q=根节点&limit=10")
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert any(item["id"] == SEED["node_id"] for item in search_results)


def test_02_auth_and_interaction_flow(client: TestClient):
    suffix = uuid4().hex[:8]
    email = f"user_{suffix}@example.com"
    username = f"writer_{suffix}"
    password = "Abcd1234"

    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert register_resp.status_code == 200, register_resp.text

    send_code_resp = client.post(
        "/api/v1/auth/send-code-for-activation",
        json={"email": email},
    )
    assert send_code_resp.status_code == 200, send_code_resp.text

    code = run(_latest_register_code(email))

    verify_resp = client.post(
        "/api/v1/auth/verify-email-for-activation",
        json={"email": email, "code": code},
    )
    assert verify_resp.status_code == 200, verify_resp.text

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200, me_resp.text
    me_data = me_resp.json()
    assert me_data["email"] == email

    like_resp = client.post(f"/api/v1/interaction/node/{SEED['node_id']}/like", headers=headers)
    assert like_resp.status_code == 200, like_resp.text
    assert like_resp.json()["status"] == "success"

    comment_resp = client.post(
        f"/api/v1/interaction/node/{SEED['node_id']}/comment",
        json={"content": "test_0227 评论内容"},
        headers=headers,
    )
    assert comment_resp.status_code == 200, comment_resp.text

    notifications_resp = client.get("/api/v1/interaction/notifications", headers=headers)
    assert notifications_resp.status_code == 200, notifications_resp.text
