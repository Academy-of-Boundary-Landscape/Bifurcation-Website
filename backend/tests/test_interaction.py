from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException

from app.api.v1.interaction import (
    create_node_comment,
    get_unread_notifications_count,
    mark_notification_read,
    mark_notifications_read,
    toggle_node_like,
)
from app.models.interaction import Notification, StoryComment
from app.models.story import NodeStatus, NodeVisibility, StoryNode
from app.models.user import User, UserRole
from app.schemas.interaction import CommentCreate

from tests.test_support import BackendAsyncTestCase, ExecuteResult, mock_request as _mock_request


class TestInteractionFlows(BackendAsyncTestCase):
    async def test_toggle_node_like_creates_like_and_notification(self) -> None:
        author = User(
            id=1,
            email="author@example.com",
            username="author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        current_user = User(
            id=2,
            email="liker@example.com",
            username="liker",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        node = StoryNode(
            id=11,
            book_id=8,
            root_id=11,
            author_id=author.id,
            title="Node",
            content="node content",
            word_count=12,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
            likes_count=0,
            freeze_interactions=False,
        )

        db = AsyncMock()
        db.get = AsyncMock(return_value=node)
        # 点赞数现在用原子 SQL 自增 + 提交后重新查询；mock 让重新查询的 scalar() 返回 1
        db.execute = AsyncMock(return_value=ExecuteResult(first=None, scalar=1))
        db.add = Mock()
        db.commit = AsyncMock()

        with patch("app.services.interactions.send_notification", AsyncMock()) as notify_mock:
            payload = await toggle_node_like(request=_mock_request(), node_id=node.id, current_user=current_user, db=db)

        self.assertEqual(payload["action"], "liked")
        self.assertEqual(payload["likes_count"], 1)
        db.add.assert_called()
        db.commit.assert_awaited_once()
        notify_mock.assert_awaited_once()

    async def test_create_node_comment_updates_counter_and_returns_comment(self) -> None:
        author = User(
            id=1,
            email="author@example.com",
            username="author",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        current_user = User(
            id=2,
            email="commenter@example.com",
            username="commenter",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        node = StoryNode(
            id=12,
            book_id=8,
            root_id=12,
            author_id=author.id,
            title="Node",
            content="node content",
            word_count=12,
            status=NodeStatus.PUBLISHED,
            visibility=NodeVisibility.PUBLIC,
            comments_count=0,
            freeze_interactions=False,
        )
        comment = StoryComment(
            id=21,
            node_id=node.id,
            book_id=node.book_id,
            user_id=current_user.id,
            content="Great branch",
            created_at=datetime.now(timezone.utc),
        )
        comment.user = current_user

        db = AsyncMock()
        db.get = AsyncMock(return_value=node)
        db.add = Mock()
        db.commit = AsyncMock()

        async def refresh_side_effect(obj):
            obj.id = 21

        db.refresh = AsyncMock(side_effect=refresh_side_effect)
        db.execute = AsyncMock(return_value=ExecuteResult(first=comment))

        with patch("app.services.interactions.send_notification", AsyncMock()) as notify_mock:
            result = await create_node_comment(
                request=_mock_request(),
                node_id=node.id,
                comment_in=CommentCreate(content="  Great branch  "),
                current_user=current_user,
                db=db,
            )

        self.assertEqual(result.id, 21)
        self.assertEqual(result.content, "Great branch")
        # comments_count 现在用原子 SQL 自增（不再就地修改 ORM 对象）；真实计数行为由 SQLite 集成测试覆盖
        db.execute.assert_awaited()
        db.commit.assert_awaited_once()
        notify_mock.assert_awaited_once()

    async def test_get_unread_notifications_count_returns_scalar(self) -> None:
        current_user = User(
            id=2,
            email="reader@example.com",
            username="reader",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        db = AsyncMock()
        db.execute = AsyncMock(return_value=ExecuteResult(scalar=6))

        payload = await get_unread_notifications_count(current_user=current_user, db=db)

        self.assertEqual(payload["unread_count"], 6)

    async def test_mark_notification_read_only_marks_owner_notification(self) -> None:
        current_user = User(
            id=2,
            email="reader@example.com",
            username="reader",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        notification = Notification(
            id=31,
            user_id=current_user.id,
            type="liked",
            node_id=8,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

        db = AsyncMock()
        db.get = AsyncMock(return_value=notification)
        db.add = Mock()
        db.commit = AsyncMock()

        payload = await mark_notification_read(
            notification_id=notification.id,
            current_user=current_user,
            db=db,
        )

        self.assertEqual(payload["detail"], "通知已标记为已读")
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        db.commit.assert_awaited_once()

    async def test_mark_notifications_read_executes_bulk_update(self) -> None:
        current_user = User(
            id=2,
            email="reader@example.com",
            username="reader",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()

        payload = await mark_notifications_read(current_user=current_user, db=db)

        self.assertEqual(payload["detail"], "全部通知已标记为已读")
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    async def test_mark_notification_read_rejects_other_users_notification(self) -> None:
        current_user = User(
            id=2,
            email="reader@example.com",
            username="reader",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        notification = Notification(
            id=32,
            user_id=999,
            type="liked",
            node_id=8,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db = AsyncMock()
        db.get = AsyncMock(return_value=notification)

        with self.assertRaises(HTTPException) as ctx:
            await mark_notification_read(
                notification_id=notification.id,
                current_user=current_user,
                db=db,
            )

        self.assertEqual(ctx.exception.status_code, 404)
