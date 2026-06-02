from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException, Response

from app.api.v1.admin import admin_dashboard_stats, audit_node
from app.api.v1.discovery import get_featured_nodes, get_latest_feed, get_trending_nodes, search_nodes
from app.api.v1.story import create_story_node, get_node_detail, read_user_nodes
from app.api.v1.users import read_user_profile
from app.models.story import NodeStatus, NodeVisibility, NodeZone, StoryNode
from app.models.story_book import BookPhase, StoryBook
from app.models.user import User, UserRole
from app.schemas.story import NodeAuditRequest, StoryNodeCreate

from tests.test_support import BackendAsyncTestCase, ExecuteResult


class TestStoryVisibilityAndAudit(BackendAsyncTestCase):
    async def test_pending_node_detail_visibility(self) -> None:
        author = User(
            id=1,
            email="author@example.com",
            username="author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        _now = datetime.now(timezone.utc)
        node = StoryNode(
            id=9,
            book_id=1,
            root_id=9,
            author_id=author.id,
            title="Pending Node",
            content="Pending content",
            word_count=15,
            status=NodeStatus.PENDING,
            visibility=NodeVisibility.PRIVATE,
            zone=NodeZone.SHORT,
            likes_count=0,
            comments_count=0,
            children_count=0,
            is_ending=False,
            freeze_interactions=False,
            is_featured=False,
            created_at=_now,
            updated_at=_now,
        )
        node.author = author

        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(first=node))

        with self.assertRaises(HTTPException) as guest_ctx:
            await get_node_detail(node_id=node.id, current_user=None, db=db)
        self.assertEqual(guest_ctx.exception.status_code, 403)

        result = await get_node_detail(node_id=node.id, current_user=author, db=db)
        self.assertEqual(result.id, node.id)

    async def test_create_story_node_rejects_branching_from_pending_parent_for_writer(self) -> None:
        writer = User(
            id=2,
            email="writer@example.com",
            username="writer",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        book = StoryBook(
            id=3,
            title="Test Book",
            phase=BookPhase.WRITING,
            allow_new_nodes=True,
        )
        parent_node = StoryNode(
            id=10,
            book_id=book.id,
            root_id=10,
            author_id=99,
            title="Parent",
            content="Parent content",
            word_count=20,
            status=NodeStatus.PENDING,
            visibility=NodeVisibility.PRIVATE,
            freeze_interactions=False,
            is_ending=False,
        )

        db = AsyncMock()
        db.get = AsyncMock(side_effect=[book, parent_node])

        with self.assertRaises(HTTPException) as ctx:
            await create_story_node(
                node_in=StoryNodeCreate(
                    book_id=book.id,
                    parent_id=parent_node.id,
                    content="Child content is valid.",
                    title="Child",
                ),
                current_user=writer,
                db=db,
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("未发布节点", ctx.exception.detail)

    async def test_admin_audit_publishes_node_and_sends_notification(self) -> None:
        admin = User(
            id=1,
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password="",
        )
        node = StoryNode(
            id=8,
            book_id=5,
            root_id=8,
            author_id=4,
            title="Pending Node",
            content="Pending content",
            word_count=15,
            status=NodeStatus.PENDING,
            visibility=NodeVisibility.PRIVATE,
        )
        node.author = User(
            id=4,
            email="author@example.com",
            username="author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )

        db = AsyncMock()
        db.get = AsyncMock(return_value=node)
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(first=node))

        with patch("app.services.story_nodes.send_notification", AsyncMock()) as send_notification_mock:
            result = await audit_node(
                node_id=node.id,
                audit_in=NodeAuditRequest(status=NodeStatus.PUBLISHED),
                db=db,
                current_user=admin,
            )

        self.assertEqual(result.status, NodeStatus.PUBLISHED)
        self.assertEqual(result.visibility, NodeVisibility.PUBLIC)
        self.assertEqual(result.reviewed_by, admin.id)
        self.assertIsInstance(result.reviewed_at, datetime)
        self.assertEqual(result.reviewed_at.tzinfo, timezone.utc)
        send_notification_mock.assert_awaited_once()
        kwargs = send_notification_mock.await_args.kwargs
        self.assertEqual(kwargs["receiver_id"], node.author_id)
        self.assertEqual(kwargs["type"].value, "approved")
        self.assertEqual(kwargs["node_id"], node.id)

    async def test_read_user_nodes_guest_only_gets_published(self) -> None:
        published_node = StoryNode(
            id=21,
            book_id=1,
            root_id=21,
            author_id=6,
            title="Published",
            content="published content",
            word_count=17,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
        )
        pending_node = StoryNode(
            id=22,
            book_id=1,
            root_id=22,
            author_id=6,
            title="Pending",
            content="pending content",
            word_count=15,
            status=NodeStatus.PENDING,
            visibility=NodeVisibility.PRIVATE,
        )

        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(all_items=[published_node]))

        result = await read_user_nodes(
            user_id=6,
            status=None,
            skip=0,
            limit=50,
            current_user=None,
            db=db,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, NodeStatus.PUBLISHED)
        self.assertNotEqual(result[0].id, pending_node.id)

    async def test_read_user_nodes_self_can_filter_pending(self) -> None:
        current_user = User(
            id=6,
            email="self@example.com",
            username="self_user",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        pending_node = StoryNode(
            id=22,
            book_id=1,
            root_id=22,
            author_id=6,
            title="Pending",
            content="pending content",
            word_count=15,
            status=NodeStatus.PENDING,
            visibility=NodeVisibility.PRIVATE,
        )

        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(all_items=[pending_node]))

        result = await read_user_nodes(
            user_id=6,
            status=NodeStatus.PENDING,
            skip=0,
            limit=50,
            current_user=current_user,
            db=db,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].status, NodeStatus.PENDING)

    async def test_admin_dashboard_stats_returns_grouped_counts(self) -> None:
        admin = User(
            id=1,
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password="",
        )
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                ExecuteResult(scalar=10),  # users_total
                ExecuteResult(scalar=1),   # users_banned (新增)
                ExecuteResult(scalar=7),   # users_active（已排除封禁）
                ExecuteResult(scalar=20),  # nodes_total
                ExecuteResult(scalar=3),   # nodes_pending
                ExecuteResult(scalar=14),  # nodes_published
                ExecuteResult(scalar=3),   # nodes_archived
                ExecuteResult(scalar=8),   # new_nodes_7d
                ExecuteResult(scalar=2),   # new_users_7d
            ]
        )

        payload = await admin_dashboard_stats(db=db, current_user=admin)

        self.assertEqual(payload["users"]["total"], 10)
        self.assertEqual(payload["users"]["active"], 7)
        self.assertEqual(payload["users"]["banned"], 1)
        # inactive = total - active - banned = 10 - 7 - 1
        self.assertEqual(payload["users"]["inactive"], 2)
        self.assertEqual(payload["users"]["new_7d"], 2)
        self.assertEqual(payload["nodes"]["total"], 20)
        self.assertEqual(payload["nodes"]["pending"], 3)
        self.assertEqual(payload["nodes"]["published"], 14)
        self.assertEqual(payload["nodes"]["archived"], 3)
        self.assertEqual(payload["nodes"]["new_7d"], 8)

    async def test_read_user_profile_returns_published_stats(self) -> None:
        now = datetime.now(timezone.utc)
        user = User(
            id=30,
            email="profile@example.com",
            username="profile_user",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
            created_at=now,
            updated_at=now,
            bio="hello",
            avatar="https://example.com/a.png",
        )
        db = AsyncMock()
        db.get = AsyncMock(return_value=user)
        db.execute = AsyncMock(
            side_effect=[
                ExecuteResult(scalar=4),
                ExecuteResult(scalar=12),
            ]
        )

        profile = await read_user_profile(user_id=user.id, db=db)

        self.assertEqual(profile.id, user.id)
        self.assertEqual(profile.nodes_count, 4)
        self.assertEqual(profile.likes_count, 12)
        self.assertEqual(profile.username, "profile_user")

    async def test_latest_feed_returns_db_scalars(self) -> None:
        author = User(
            id=41,
            email="feed@example.com",
            username="feed_author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        node = StoryNode(
            id=51,
            book_id=2,
            root_id=51,
            author_id=author.id,
            title="Feed Node",
            content="feed content",
            word_count=12,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
        )
        node.author = author

        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(all_items=[node]))

        result = await get_latest_feed(response=Response(), book_id=None, skip=0, limit=20, db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, node.id)

    async def test_featured_nodes_returns_ranked_featured_entries(self) -> None:
        author = User(
            id=44,
            email="featured@example.com",
            username="featured_author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        ranked_node = StoryNode(
            id=81,
            book_id=2,
            root_id=81,
            author_id=author.id,
            title="Featured Ranked",
            content="featured content",
            word_count=16,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
            is_featured=True,
            feature_rank=1,
        )
        ranked_node.author = author
        unranked_node = StoryNode(
            id=82,
            book_id=2,
            root_id=82,
            author_id=author.id,
            title="Featured Later",
            content="later featured content",
            word_count=18,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
            is_featured=True,
            feature_rank=None,
        )
        unranked_node.author = author

        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(all_items=[ranked_node, unranked_node]))

        result = await get_featured_nodes(response=Response(), limit=6, db=db)

        self.assertEqual([node.id for node in result], [81, 82])
        self.assertTrue(all(node.is_featured for node in result))

    async def test_trending_nodes_falls_back_when_recent_pool_is_small(self) -> None:
        author = User(
            id=42,
            email="trend@example.com",
            username="trend_author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        node = StoryNode(
            id=61,
            book_id=2,
            root_id=61,
            author_id=author.id,
            title="Hot Node",
            content="hot content",
            word_count=11,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
            likes_count=99,
        )
        node.author = author

        db = AsyncMock()
        # 新流程：窗口计数(1) -> 因 <3 触发兜底 -> 全站计数(2) -> 取行(3)
        db.execute = AsyncMock(
            side_effect=[
                ExecuteResult(scalar=1),            # 窗口内总数 < 3
                ExecuteResult(scalar=5),            # 全站已发布总数
                ExecuteResult(all_items=[node]),    # 兜底榜单行
            ]
        )

        result = await get_trending_nodes(response=Response(), days=7, limit=10, db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].likes_count, 99)
        self.assertEqual(db.execute.await_count, 3)

    async def test_search_nodes_returns_matching_published_nodes(self) -> None:
        author = User(
            id=43,
            email="search@example.com",
            username="search_author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        node = StoryNode(
            id=71,
            book_id=2,
            root_id=71,
            author_id=author.id,
            title="Quantum Branch",
            content="search content",
            word_count=14,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
        )
        node.author = author

        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(all_items=[node]))

        result = await search_nodes(response=Response(), q="Quantum", limit=20, db=db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Quantum Branch")
