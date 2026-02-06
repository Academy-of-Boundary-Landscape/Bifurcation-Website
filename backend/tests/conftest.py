# tests/conftest.py
import time
import requests

BASE_URL = "http://localhost:8057"

LOGIN_URL = f"{BASE_URL}/auth/login"

USERNAME = "admin@example.com"
PASSWORD = "admin123"

TOKEN_CACHE = {"token": None, "exp": 0}


def get_token():
    now = time.time()
    if TOKEN_CACHE["token"] and TOKEN_CACHE["exp"] > now:
        return TOKEN_CACHE["token"]

    resp = requests.post(
        LOGIN_URL,
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    resp.raise_for_status()

    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Login response missing access_token")

    # 假设 token 30 分钟过期
    TOKEN_CACHE["token"] = token
    TOKEN_CACHE["exp"] = now + 25 * 60
    return token
