from __future__ import annotations

from datetime import timedelta

from app.core.security import create_access_token
from app.models.story import NodeLike, NodeStatus, NodeVisibility, StoryNode
from app.models.story_book import BookPhase, StoryBook
from app.models.user import User, UserRole

from tests.test_support import SQLiteIntegrationTestCase


class TestMetricsIntegrity(SQLiteIntegrationTestCase):
    def _auth(self, user_id: int) -> dict[str, str]:
        token = create_access_token(subject=str(user_id), expires_delta=timedelta(minutes=30))
        return {"Authorization": f"Bearer {token}"}

    async def test_like_toggle_never_goes_negative_and_matches_rows(self) -> None:
        with self.db_session() as s:
            book = StoryBook(title="B", phase=BookPhase.WRITING, allow_new_nodes=True)
            author = User(email="a@x.com", username="aaa", role=UserRole.WRITER, is_active=True)
            liker = User(email="l@x.com", username="liker", role=UserRole.WRITER, is_active=True)
            s.add_all([book, author, liker])
            s.flush()
            node = StoryNode(
                book_id=book.id, root_id=0, author_id=author.id, title="N", content="c",
                word_count=1, status=NodeStatus.PUBLISHED, visibility=NodeVisibility.PUBLIC,
                likes_count=0,
            )
            s.add(node)
            s.flush()
            node.root_id = node.id
            s.commit()
            node_id, liker_id = node.id, liker.id

        # like
        r1 = await self.client.post(f"/api/v1/interaction/node/{node_id}/like", headers=self._auth(liker_id))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["action"], "liked")
        self.assertEqual(r1.json()["likes_count"], 1)
        # unlike
        r2 = await self.client.post(f"/api/v1/interaction/node/{node_id}/like", headers=self._auth(liker_id))
        self.assertEqual(r2.json()["action"], "unliked")
        self.assertEqual(r2.json()["likes_count"], 0)
        # like again
        r3 = await self.client.post(f"/api/v1/interaction/node/{node_id}/like", headers=self._auth(liker_id))
        self.assertEqual(r3.json()["likes_count"], 1)

        with self.db_session() as s:
            node = s.get(StoryNode, node_id)
            rows = s.query(NodeLike).filter(NodeLike.node_id == node_id).count()
            self.assertEqual(node.likes_count, 1)
            self.assertEqual(node.likes_count, rows)

    async def test_children_count_excludes_archived(self) -> None:
        with self.db_session() as s:
            book = StoryBook(title="B", phase=BookPhase.WRITING, allow_new_nodes=True)
            admin = User(email="adm@x.com", username="adm", role=UserRole.ADMIN, is_active=True)
            writer = User(email="w@x.com", username="writeruser", role=UserRole.WRITER, is_active=True)
            s.add_all([book, admin, writer])
            s.flush()
            parent = StoryNode(
                book_id=book.id, root_id=0, author_id=admin.id, title="P", content="c",
                word_count=1, status=NodeStatus.PUBLISHED, visibility=NodeVisibility.PUBLIC,
                children_count=0,
            )
            s.add(parent)
            s.flush()
            parent.root_id = parent.id
            s.commit()
            book_id, parent_id, writer_id, admin_id = book.id, parent.id, writer.id, admin.id

        # writer creates two pending children
        child_ids = []
        for i in range(2):
            r = await self.client.post(
                "/api/v1/story/node",
                headers=self._auth(writer_id),
                json={"book_id": book_id, "parent_id": parent_id, "content": f"child {i} body", "zone": "short"},
            )
            self.assertEqual(r.status_code, 200, r.text)
            child_ids.append(r.json()["id"])

        with self.db_session() as s:
            self.assertEqual(s.get(StoryNode, parent_id).children_count, 2)

        # admin archives one child -> children_count drops to 1
        ra = await self.client.patch(
            f"/api/v1/admin/nodes/{child_ids[0]}/audit",
            headers=self._auth(admin_id),
            json={"status": "archived", "reject_reason": "test"},
        )
        self.assertEqual(ra.status_code, 200, ra.text)
        with self.db_session() as s:
            self.assertEqual(s.get(StoryNode, parent_id).children_count, 1)

        # admin re-publishes it -> back to 2
        rp = await self.client.patch(
            f"/api/v1/admin/nodes/{child_ids[0]}/audit",
            headers=self._auth(admin_id),
            json={"status": "published"},
        )
        self.assertEqual(rp.status_code, 200, rp.text)
        with self.db_session() as s:
            self.assertEqual(s.get(StoryNode, parent_id).children_count, 2)

    async def test_nodes_count_consistent_between_me_and_public(self) -> None:
        with self.db_session() as s:
            book = StoryBook(title="B", phase=BookPhase.WRITING, allow_new_nodes=True)
            user = User(email="u@x.com", username="useruu", role=UserRole.WRITER, is_active=True)
            s.add_all([book, user])
            s.flush()
            published = StoryNode(
                book_id=book.id, root_id=0, author_id=user.id, title="pub", content="c",
                word_count=1, status=NodeStatus.PUBLISHED, visibility=NodeVisibility.PUBLIC,
            )
            pending = StoryNode(
                book_id=book.id, root_id=0, author_id=user.id, title="pend", content="c",
                word_count=1, status=NodeStatus.PENDING, visibility=NodeVisibility.PRIVATE,
            )
            s.add_all([published, pending])
            s.flush()
            published.root_id = published.id
            pending.root_id = pending.id
            s.commit()
            user_id = user.id

        me = await self.client.get("/api/v1/auth/me", headers=self._auth(user_id))
        pub = await self.client.get(f"/api/v1/users/{user_id}")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(pub.status_code, 200)
        # 两端口径一致：均为已发布节点数
        self.assertEqual(me.json()["nodes_count"], 1)
        self.assertEqual(me.json()["nodes_count"], pub.json()["nodes_count"])

    async def test_list_endpoints_expose_real_total_via_header(self) -> None:
        # 建 5 个已发布节点，limit=2 仍应通过 X-Total-Count 暴露真实总数 5
        with self.db_session() as s:
            book = StoryBook(title="B", phase=BookPhase.WRITING, allow_new_nodes=True)
            author = User(email="a@x.com", username="aaa", role=UserRole.WRITER, is_active=True)
            s.add_all([book, author])
            s.flush()
            for i in range(5):
                n = StoryNode(
                    book_id=book.id, root_id=0, author_id=author.id, title=f"N{i}",
                    content="quantum branch content", word_count=3,
                    status=NodeStatus.PUBLISHED, visibility=NodeVisibility.PUBLIC,
                )
                s.add(n)
                s.flush()
                n.root_id = n.id
            s.commit()

        feed = await self.client.get("/api/v1/discovery/feed?limit=2")
        self.assertEqual(feed.status_code, 200)
        self.assertEqual(len(feed.json()), 2)
        self.assertEqual(feed.headers.get("x-total-count"), "5")

        search = await self.client.get("/api/v1/discovery/search?q=quantum&limit=2")
        self.assertEqual(search.headers.get("x-total-count"), "5")

    async def test_admin_stats_excludes_banned_from_active(self) -> None:
        with self.db_session() as s:
            admin = User(email="adm@x.com", username="adm", role=UserRole.ADMIN, is_active=True)
            writer = User(email="w@x.com", username="writeruser", role=UserRole.WRITER, is_active=True)
            inactive = User(email="i@x.com", username="inactiveu", role=UserRole.WRITER, is_active=False)
            banned = User(email="b@x.com", username="banneduser", role=UserRole.BANNED, is_active=True)
            s.add_all([admin, writer, inactive, banned])
            s.commit()
            admin_id = admin.id

        r = await self.client.get("/api/v1/admin/stats", headers=self._auth(admin_id))
        self.assertEqual(r.status_code, 200, r.text)
        users = r.json()["users"]
        self.assertEqual(users["total"], 4)
        # active 排除 banned（admin + writer = 2）
        self.assertEqual(users["active"], 2)
        self.assertEqual(users["banned"], 1)
