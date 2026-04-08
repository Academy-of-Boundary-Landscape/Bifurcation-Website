from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token
from app.models.interaction import Notification, NotificationType, StoryComment
from app.models.story import NodeLike, NodeStatus, NodeVisibility, StoryNode
from app.models.story_book import BookPhase, StoryBook
from app.models.user import User, UserRole

from tests.test_support import SQLiteIntegrationTestCase


class TestSQLiteApiIntegration(SQLiteIntegrationTestCase):
    def _auth_headers(self, user_id: int) -> dict[str, str]:
        token = create_access_token(subject=str(user_id), expires_delta=timedelta(minutes=30))
        return {"Authorization": f"Bearer {token}"}

    async def test_auth_me_returns_real_profile_counts(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Profile Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            user = User(
                email="reader@example.com",
                username="reader",
                role=UserRole.WRITER,
                is_active=True,
            )
            liker = User(
                email="liker@example.com",
                username="liker",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, user, liker])
            session.flush()

            node = StoryNode(
                book_id=book.id,
                parent_id=None,
                root_id=0,
                author_id=user.id,
                title="Node 1",
                content="content",
                word_count=7,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
            )
            session.add(node)
            session.flush()
            node.root_id = node.id
            session.add(NodeLike(user_id=liker.id, node_id=node.id))
            session.commit()
            user_id = user.id

        response = await self.client.get("/api/v1/auth/me", headers=self._auth_headers(user_id))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["username"], "reader")
        self.assertEqual(payload["nodes_count"], 1)
        self.assertEqual(payload["likes_count"], 1)

    async def test_story_tree_and_node_detail_apply_visibility_rules(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Vis Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            author = User(
                email="author@example.com",
                username="author",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, author])
            session.flush()

            published = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Published",
                content="published content",
                word_count=17,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
            )
            pending = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Pending",
                content="pending content",
                word_count=15,
                status=NodeStatus.PENDING,
                visibility=NodeVisibility.PRIVATE,
            )
            session.add_all([published, pending])
            session.flush()
            published.root_id = published.id
            pending.root_id = pending.id
            session.commit()

            book_id = book.id
            author_id = author.id
            published_id = published.id
            pending_id = pending.id

        guest_tree = await self.client.get(f"/api/v1/story/tree?book_id={book_id}")
        self.assertEqual(guest_tree.status_code, 200)
        self.assertEqual([item["id"] for item in guest_tree.json()], [published_id])

        guest_pending = await self.client.get(f"/api/v1/story/node/{pending_id}")
        self.assertEqual(guest_pending.status_code, 403)

        author_tree = await self.client.get(
            f"/api/v1/story/tree?book_id={book_id}",
            headers=self._auth_headers(author_id),
        )
        self.assertEqual(author_tree.status_code, 200)
        self.assertEqual({item["id"] for item in author_tree.json()}, {published_id, pending_id})

        author_pending = await self.client.get(
            f"/api/v1/story/node/{pending_id}",
            headers=self._auth_headers(author_id),
        )
        self.assertEqual(author_pending.status_code, 200)
        self.assertEqual(author_pending.json()["status"], "pending")

    async def test_admin_story_tree_keeps_archived_root_with_children(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Archived Root Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            admin = User(
                email="admin-root@example.com",
                username="admin_root",
                role=UserRole.ADMIN,
                is_active=True,
            )
            author = User(
                email="author-root@example.com",
                username="author_root",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, admin, author])
            session.flush()

            root = StoryNode(
                book_id=book.id,
                parent_id=None,
                root_id=0,
                author_id=author.id,
                title="Archived Root",
                content="archived root content",
                word_count=21,
                status=NodeStatus.ARCHIVED,
                visibility=NodeVisibility.PRIVATE,
                children_count=2,
            )
            session.add(root)
            session.flush()
            root.root_id = root.id

            child_one = StoryNode(
                book_id=book.id,
                parent_id=root.id,
                root_id=root.id,
                author_id=author.id,
                title="Child One",
                content="child one content",
                word_count=17,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
            )
            child_two = StoryNode(
                book_id=book.id,
                parent_id=root.id,
                root_id=root.id,
                author_id=author.id,
                title="Child Two",
                content="child two content",
                word_count=17,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
            )
            session.add_all([child_one, child_two])
            session.commit()

            book_id = book.id
            admin_id = admin.id
            root_id = root.id

        response = await self.client.get(
            f"/api/v1/story/tree?book_id={book_id}",
            headers=self._auth_headers(admin_id),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], root_id)
        self.assertEqual(payload[0]["status"], "archived")
        self.assertEqual({child["title"] for child in payload[0]["children"]}, {"Child One", "Child Two"})

    async def test_optional_auth_tree_keeps_logged_in_admin_even_if_not_verified(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Optional Auth Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            admin = User(
                email="admin-unverified@example.com",
                username="admin_unverified",
                role=UserRole.ADMIN,
                is_active=True,
            )
            author = User(
                email="author-unverified@example.com",
                username="author_unverified",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, admin, author])
            session.flush()

            root = StoryNode(
                book_id=book.id,
                parent_id=None,
                root_id=0,
                author_id=author.id,
                title="Archived Root Optional",
                content="archived root content",
                word_count=21,
                status=NodeStatus.ARCHIVED,
                visibility=NodeVisibility.PRIVATE,
            )
            session.add(root)
            session.flush()
            root.root_id = root.id
            session.commit()

            book_id = book.id
            admin_id = admin.id
            root_id = root.id

        response = await self.client.get(
            f"/api/v1/story/tree?book_id={book_id}",
            headers=self._auth_headers(admin_id),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["id"] for item in payload], [root_id])

    async def test_discovery_featured_returns_only_published_featured_nodes(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Featured Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            author = User(
                email="featured-writer@example.com",
                username="featured_writer",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, author])
            session.flush()

            first_featured = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Featured First",
                content="featured first content",
                word_count=22,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
                is_featured=True,
                feature_rank=1,
                published_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            second_featured = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Featured Second",
                content="featured second content",
                word_count=24,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
                is_featured=True,
                feature_rank=2,
                published_at=datetime.now(timezone.utc),
            )
            hidden_featured = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Pending Featured",
                content="pending featured content",
                word_count=18,
                status=NodeStatus.PENDING,
                visibility=NodeVisibility.PRIVATE,
                is_featured=True,
                feature_rank=0,
            )
            regular_node = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Regular Node",
                content="regular content",
                word_count=20,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
                is_featured=False,
            )
            session.add_all([first_featured, second_featured, hidden_featured, regular_node])
            session.flush()
            first_featured.root_id = first_featured.id
            second_featured.root_id = second_featured.id
            hidden_featured.root_id = hidden_featured.id
            regular_node.root_id = regular_node.id
            session.commit()

        response = await self.client.get("/api/v1/discovery/featured?limit=6")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["title"] for item in payload], ["Featured First", "Featured Second"])
        self.assertTrue(all(item["is_featured"] for item in payload))
        self.assertTrue(all(item["status"] == "published" for item in payload))

    async def test_comment_creation_and_like_toggle_write_real_rows(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Interaction Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            author = User(
                email="author2@example.com",
                username="author2",
                role=UserRole.WRITER,
                is_active=True,
            )
            actor = User(
                email="actor@example.com",
                username="actor",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, author, actor])
            session.flush()

            node = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Interactive",
                content="node content",
                word_count=12,
                status=NodeStatus.PUBLISHED,
                visibility=NodeVisibility.PUBLIC,
                comments_count=0,
                likes_count=0,
                freeze_interactions=False,
            )
            session.add(node)
            session.flush()
            node.root_id = node.id
            session.commit()

            node_id = node.id
            actor_id = actor.id
            author_id = author.id

        comment_response = await self.client.post(
            f"/api/v1/interaction/node/{node_id}/comment",
            headers=self._auth_headers(actor_id),
            json={"content": "Nice branch"},
        )
        self.assertEqual(comment_response.status_code, 200)
        self.assertEqual(comment_response.json()["content"], "Nice branch")

        like_response = await self.client.post(
            f"/api/v1/interaction/node/{node_id}/like",
            headers=self._auth_headers(actor_id),
        )
        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(like_response.json()["action"], "liked")

        with self.db_session() as session:
            node = session.get(StoryNode, node_id)
            comments = session.query(StoryComment).filter(StoryComment.node_id == node_id).all()
            notifications = (
                session.query(Notification)
                .filter(Notification.user_id == author_id)
                .order_by(Notification.id)
                .all()
            )

        self.assertEqual(node.comments_count, 1)
        self.assertEqual(node.likes_count, 1)
        self.assertEqual(len(comments), 1)
        self.assertEqual(len(notifications), 2)
        self.assertEqual({item.type for item in notifications}, {NotificationType.COMMENTED, NotificationType.LIKED})

    async def test_admin_audit_endpoint_publishes_node_and_creates_notification(self) -> None:
        with self.db_session() as session:
            book = StoryBook(title="Audit Book", phase=BookPhase.WRITING, allow_new_nodes=True)
            admin = User(
                email="admin@example.com",
                username="admin_user",
                role=UserRole.ADMIN,
                is_active=True,
            )
            author = User(
                email="writer@example.com",
                username="writer_user",
                role=UserRole.WRITER,
                is_active=True,
            )
            session.add_all([book, admin, author])
            session.flush()

            node = StoryNode(
                book_id=book.id,
                root_id=0,
                author_id=author.id,
                title="Pending Node",
                content="pending node content",
                word_count=20,
                status=NodeStatus.PENDING,
                visibility=NodeVisibility.PRIVATE,
                created_at=datetime.now(timezone.utc),
            )
            session.add(node)
            session.flush()
            node.root_id = node.id
            session.commit()

            node_id = node.id
            admin_id = admin.id
            author_id = author.id

        response = await self.client.patch(
            f"/api/v1/admin/nodes/{node_id}/audit",
            headers=self._auth_headers(admin_id),
            json={"status": "published"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "published")
        self.assertEqual(payload["visibility"], "public")

        with self.db_session() as session:
            node = session.get(StoryNode, node_id)
            notification = (
                session.query(Notification)
                .filter(Notification.user_id == author_id)
                .order_by(Notification.id.desc())
                .first()
            )

        self.assertEqual(node.status, NodeStatus.PUBLISHED)
        self.assertEqual(node.visibility, NodeVisibility.PUBLIC)
        self.assertEqual(node.reviewed_by, admin_id)
        self.assertIsNotNone(notification)
        self.assertEqual(notification.type, NotificationType.APPROVED)
