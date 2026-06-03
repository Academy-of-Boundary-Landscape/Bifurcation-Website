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


if __name__ == "__main__":
    unittest.main()
