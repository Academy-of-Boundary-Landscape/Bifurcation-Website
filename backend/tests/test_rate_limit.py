from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.rate_limit import get_client_ip, user_or_ip_key


def _req(*, headers=None, host="127.0.0.1", user_id=None):
    state = SimpleNamespace()
    if user_id is not None:
        state.rate_limit_user_id = user_id
    return SimpleNamespace(
        headers={k.lower(): v for k, v in (headers or {}).items()},
        client=SimpleNamespace(host=host),
        state=state,
    )


class TestRateLimitKeys(unittest.TestCase):
    def test_client_ip_prefers_xff_first_hop(self):
        req = _req(headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}, host="127.0.0.1")
        self.assertEqual(get_client_ip(req), "203.0.113.7")

    def test_client_ip_falls_back_to_real_ip_then_client(self):
        self.assertEqual(get_client_ip(_req(headers={"X-Real-IP": "198.51.100.9"})), "198.51.100.9")
        self.assertEqual(get_client_ip(_req(host="192.0.2.5")), "192.0.2.5")

    def test_user_key_prefers_user_then_ip(self):
        self.assertEqual(user_or_ip_key(_req(user_id=42)), "user:42")
        self.assertEqual(user_or_ip_key(_req(host="192.0.2.5")), "192.0.2.5")


from datetime import timedelta

from app.core.security import create_access_token
from app.core.rate_limit import limiter, COMMENT_LIMIT
from app.models.story import NodeStatus, NodeVisibility, StoryNode
from app.models.story_book import BookPhase, StoryBook
from app.models.user import User, UserRole
from tests.test_support import SQLiteIntegrationTestCase


class TestCommentRateLimit(SQLiteIntegrationTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        limiter.reset()
        limiter.enabled = True

    async def asyncTearDown(self) -> None:
        limiter.reset()
        limiter.enabled = False
        await super().asyncTearDown()

    def _auth(self, user_id: int) -> dict[str, str]:
        token = create_access_token(subject=str(user_id), expires_delta=timedelta(minutes=30))
        return {"Authorization": f"Bearer {token}"}

    async def test_comment_rate_limit_returns_429_after_threshold(self) -> None:
        # COMMENT_LIMIT 是 "6/minute"；第 7 次应被挡
        assert COMMENT_LIMIT == "6/minute"
        with self.db_session() as s:
            book = StoryBook(title="B", phase=BookPhase.WRITING, allow_new_nodes=True)
            author = User(email="ra@x.com", username="rateauthor", role=UserRole.WRITER, is_active=True)
            commenter = User(email="rc@x.com", username="ratecommenter", role=UserRole.WRITER, is_active=True)
            s.add_all([book, author, commenter])
            s.flush()
            node = StoryNode(
                book_id=book.id, root_id=0, author_id=author.id, title="N", content="c",
                word_count=1, status=NodeStatus.PUBLISHED, visibility=NodeVisibility.PUBLIC,
            )
            s.add(node)
            s.flush()
            node.root_id = node.id
            s.commit()
            node_id, commenter_id = node.id, commenter.id

        headers = self._auth(commenter_id)
        url = f"/api/v1/interaction/node/{node_id}/comment"

        statuses = []
        for i in range(7):
            r = await self.client.post(url, json={"content": f"评论 {i}"}, headers=headers)
            statuses.append(r.status_code)

        # 前 6 次成功，第 7 次 429
        self.assertTrue(all(c == 200 for c in statuses[:6]), statuses)
        self.assertEqual(statuses[6], 429, statuses)

        last = await self.client.post(url, json={"content": "再来一条"}, headers=headers)
        self.assertEqual(last.status_code, 429)
        self.assertEqual(last.json()["detail"], "操作过于频繁，请稍后再试")
        self.assertIn("retry-after", {k.lower() for k in last.headers.keys()})


if __name__ == "__main__":
    unittest.main()
