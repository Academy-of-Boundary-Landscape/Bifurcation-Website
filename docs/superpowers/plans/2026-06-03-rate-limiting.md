# 限流（Rate Limiting）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给点赞/评论按用户、SSO 换登录态按 IP 加 slowapi 应用层限流，给写操作加 nginx 边缘 IP 限流，并在前端对 429 弹一次性提示。

**Architecture:** 两层。nginx 用 `map` 只对写方法计数、按 IP `limit_req` 粗挡（放过读请求）；FastAPI 用 slowapi per-route 装饰器，key 优先按登录用户（写到 `request.state` 再被 key_func 读取）、未登录端点按真实客户端 IP（取 `X-Forwarded-For`）。limiter 用内存存储，测试里全局关闭、专用测试里临时开启。

**Tech Stack:** FastAPI + slowapi（内存存储）、Vue 3 + Naive UI（`createDiscreteApi`）、nginx `limit_req`。

参考 spec：`docs/superpowers/specs/2026-06-03-rate-limiting-design.md`

---

## 文件结构

后端：
- Create `backend/app/core/rate_limit.py` — limiter 实例、key 函数、429 处理器、阈值常量（限流策略唯一来源）
- Modify `backend/requirements.txt` — 加 `slowapi`
- Modify `backend/app/core/config.py` — 加 `RATE_LIMIT_ENABLED`
- Modify `backend/main.py` — 接 `app.state.limiter` + 异常处理器
- Modify `backend/app/api/deps.py` — `get_current_user` 写 `request.state.rate_limit_user_id`
- Modify `backend/app/api/v1/interaction.py` — 装饰 like / comment
- Modify `backend/app/api/v1/auth.py` — 装饰 sso/exchange
- Modify `backend/tests/test_support.py` — 模块级关闭 limiter
- Create `backend/tests/test_rate_limit.py` — key 函数单测 + 429 行为测试

部署：
- Modify `deploy/nginx.conf` 与 `nginx.example.conf` — 写操作 IP 限流

前端：
- Create `frontend/src/theme.ts` — 抽出共享 `themeOverrides`
- Modify `frontend/src/App.vue` — 改 import `themeOverrides`
- Create `frontend/src/services/notify.ts` — discrete message + `notifyRateLimited`
- Modify `frontend/src/services/http.ts` — 429 分支

文档：
- Modify `docs/changelog.md`、`docs/followups.md`

---

## Task 1: 加依赖与配置开关

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: 加 slowapi 到 requirements**

在 `backend/requirements.txt` 末尾追加一行：

```
slowapi>=0.1.9
```

- [ ] **Step 2: 安装到 venv**

Run: `cd backend && venv/bin/pip install "slowapi>=0.1.9"`
Expected: 成功安装 slowapi 及其依赖 `limits`。

- [ ] **Step 3: 加配置开关**

在 `backend/app/core/config.py` 的 `Settings` 类里，`SQL_ECHO` 那一行后面加：

```python
    # 限流总开关（测试里置 False；生产默认开）
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
```

- [ ] **Step 4: 验证导入不报错**

Run: `cd backend && venv/bin/python -c "from app.core.config import settings; print(settings.RATE_LIMIT_ENABLED)"`
Expected: 打印 `True`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/core/config.py
git commit -m "chore(backend): 引入 slowapi 依赖与 RATE_LIMIT_ENABLED 开关"
```

---

## Task 2: rate_limit.py 模块 + key 函数单测（TDD）

**Files:**
- Create: `backend/app/core/rate_limit.py`
- Test: `backend/tests/test_rate_limit.py`（本任务先建文件、只放 key 函数单测）

- [ ] **Step 1: 写失败的单测**

创建 `backend/tests/test_rate_limit.py`：

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && venv/bin/python -m pytest tests/test_rate_limit.py -q`
Expected: FAIL —— `ModuleNotFoundError: No module named 'app.core.rate_limit'`

- [ ] **Step 3: 写 rate_limit.py**

创建 `backend/app/core/rate_limit.py`：

```python
"""限流策略集中处：limiter 实例、key 函数、429 处理器、阈值常量。"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

# —— 阈值 ——
LIKE_LIMIT = "60/minute"      # 切赞按用户
COMMENT_LIMIT = "6/minute"    # 发评论按用户（防灌水）
SSO_LIMIT = "10/minute"       # 换登录态按 IP（未登录）


def get_client_ip(request: Request) -> str:
    """取真实客户端 IP。后端在 nginx 后面，必须读转发头，否则全是 127.0.0.1。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    client = request.client
    return client.host if client else "unknown"


def user_or_ip_key(request: Request) -> str:
    """默认 key：登录用户优先（deps 写入 request.state），否则回退到 IP。"""
    user_id = getattr(request.state, "rate_limit_user_id", None)
    if user_id is not None:
        return f"user:{user_id}"
    return get_client_ip(request)


limiter = Limiter(key_func=user_or_ip_key, enabled=settings.RATE_LIMIT_ENABLED)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """统一 429 响应：body 用全站 {"detail": ...} 形状，并注入 Retry-After 等头。"""
    response = JSONResponse(
        status_code=429,
        content={"detail": "操作过于频繁，请稍后再试"},
    )
    # 复用 slowapi 的头注入，拿到正确的 Retry-After / X-RateLimit-*
    return request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd backend && venv/bin/python -m pytest tests/test_rate_limit.py -q`
Expected: PASS（3 个 key 函数用例通过）

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/rate_limit.py backend/tests/test_rate_limit.py
git commit -m "feat(backend): rate_limit 模块（limiter + key 函数 + 429 处理器）"
```

---

## Task 3: 测试里全局关闭 limiter（保护既有测试）

**Files:**
- Modify: `backend/tests/test_support.py`

> 必须在装饰端点（Task 6）之前做：limiter `enabled=False` 时 slowapi 直接短路、不触碰
> `request.app.state`，既不误伤现有测试，也不跨用例累积内存计数。

- [ ] **Step 1: 模块级关闭**

在 `backend/tests/test_support.py` 顶部 import 区（`BACKEND_DIR` 那段 sys.path 注入之后）加：

```python
# 测试默认关闭限流：slowapi enabled=False 时直接短路，既不误伤既有用例，
# 也不在进程内跨用例累积内存计数。专用测试 test_rate_limit.py 会临时开启。
from app.core.rate_limit import limiter as _limiter
_limiter.enabled = False
```

- [ ] **Step 2: 跑全套件确认仍全绿**

Run: `cd backend && venv/bin/python -m pytest -q`
Expected: PASS（既有 ~36 个用例全过；新增 key 函数用例也过）

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_support.py
git commit -m "test(backend): 测试环境默认关闭限流（避免误伤与跨用例污染）"
```

---

## Task 4: main.py 接线

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: import 并挂载 limiter**

在 `backend/main.py` 的 import 区加：

```python
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter, rate_limit_handler
```

在 `app = FastAPI(title=settings.PROJECT_NAME)` 之后、CORS 中间件之前加：

```python
# ==========================================
# 🚦 限流（slowapi，按用户/IP，内存存储）
# ==========================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
```

- [ ] **Step 2: 验证 app 能正常构建**

Run: `cd backend && venv/bin/python -c "import main; print('ok', hasattr(main.app.state, 'limiter'))"`
Expected: 打印 `ok True`

- [ ] **Step 3: 跑全套件确认仍全绿**

Run: `cd backend && venv/bin/python -m pytest -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat(backend): main 挂载 limiter 与 429 异常处理器"
```

---

## Task 5: deps 写入 request.state.rate_limit_user_id

**Files:**
- Modify: `backend/app/api/deps.py`

- [ ] **Step 1: 给 get_current_user 加 Request 并写 state**

把 `backend/app/api/deps.py` 顶部 import 改为带 `Request`：

```python
from fastapi import Depends, HTTPException, Request, status
```

把 `get_current_user` 的签名与返回前改成（加 `request: Request` 形参，return 前写 state）：

```python
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    # 供 slowapi key_func 按用户限流
    request.state.rate_limit_user_id = user.id
    return user
```

> 只改 `get_current_user`。`get_current_active_user` / `get_current_admin` 依赖它，自动获益。
> `get_current_user_or_none` 不改（匿名路径不需要按用户限流）。

- [ ] **Step 2: 跑全套件确认仍全绿**

Run: `cd backend && venv/bin/python -m pytest -q`
Expected: PASS（既有鉴权相关用例不受影响——FastAPI 自动注入 Request）

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/deps.py
git commit -m "feat(backend): 鉴权依赖写入 request.state.rate_limit_user_id"
```

---

## Task 6: 装饰三个端点

**Files:**
- Modify: `backend/app/api/v1/interaction.py`
- Modify: `backend/app/api/v1/auth.py`

> slowapi 硬性要求被装饰的端点形参里有名为 `request` 且类型为 `Request` 的参数。

- [ ] **Step 1: interaction.py import + 装饰 like/comment**

把 `backend/app/api/v1/interaction.py` 第 4 行的 fastapi import 加上 `Request`：

```python
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
```

在 import 区加：

```python
from app.core.rate_limit import limiter, LIKE_LIMIT, COMMENT_LIMIT
```

给 `toggle_node_like` 加装饰器与 `request` 形参：

```python
@router.post(
    "/node/{node_id}/like",
    response_model=interact_schema.LikeToggleResponse,
    summary="点赞/取消点赞 (Toggle)",
    operation_id="toggleLike",
    responses={
        200: {"description": "操作成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
@limiter.limit(LIKE_LIMIT)
async def toggle_node_like(
    request: Request,
    node_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await toggle_story_node_like(db=db, current_user=current_user, node_id=node_id)
```

给 `create_node_comment` 加装饰器与 `request` 形参：

```python
@router.post(
    "/node/{node_id}/comment",
    response_model=interact_schema.CommentResponse,
    summary="发表评论",
    operation_id="createComment",
    responses={
        200: {"description": "发表成功"},
        401: {"model": common_schema.ErrorResponse, "description": "未认证"},
        404: {"model": common_schema.ErrorResponse, "description": "节点不存在"},
        422: {"model": common_schema.ValidationErrorResponse, "description": "参数校验失败"},
    },
)
@limiter.limit(COMMENT_LIMIT)
async def create_node_comment(
    request: Request,
    node_id: int,
    comment_in: interact_schema.CommentCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await create_story_comment(
        db=db,
        current_user=current_user,
        node_id=node_id,
        comment_in=comment_in,
    )
```

> 装饰器顺序：`@router.post(...)` 在最上，`@limiter.limit(...)` 紧贴函数。`request` 放第一个形参。

- [ ] **Step 2: auth.py import + 装饰 sso/exchange（按 IP）**

把 `backend/app/api/v1/auth.py` 第 4 行 import 加 `Request`：

```python
from fastapi import APIRouter, Depends, Query, Request
```

在 import 区加：

```python
from app.core.rate_limit import limiter, get_client_ip, SSO_LIMIT
```

给 `exchange_sso_login` 加装饰器（强制按 IP）与 `request` 形参：

```python
@router.post(
    "/sso/exchange",
    response_model=sso_schema.SSOExchangeResponse,
    summary="Casdoor 授权码换取本站登录态",
)
@limiter.limit(SSO_LIMIT, key_func=get_client_ip)
async def exchange_sso_login(
    request: Request,
    payload: sso_schema.SSOExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_sso_code(db, payload.code, payload.state)
    user: User = result["user"]
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )
    return sso_schema.SSOExchangeResponse(
        access_token=access_token,
        token_type="bearer",
        redirect_to=result["redirect_to"],
        is_new_user=result["is_new_user"],
    )
```

- [ ] **Step 3: 跑全套件确认仍全绿**

Run: `cd backend && venv/bin/python -m pytest -q`
Expected: PASS（limiter 在测试里已关，装饰器短路，既有用例不受影响）

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/interaction.py backend/app/api/v1/auth.py
git commit -m "feat(backend): 给 like/comment（按用户）与 sso/exchange（按 IP）加限流"
```

---

## Task 7: 429 行为测试（开启 limiter）

**Files:**
- Modify: `backend/tests/test_rate_limit.py`（在 Task 2 的文件里追加一个集成测试类）

- [ ] **Step 1: 追加 429 集成测试**

在 `backend/tests/test_rate_limit.py` 末尾（`if __name__` 之前）追加：

```python
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
```

> 若 `create_story_comment` 返回的成功码不是 200（例如 201），把断言里的 `200` 改成实际成功码；
> 用一次手动 `curl`/读路由 `status_code` 即可确认。当前 `@router.post` 未显式设 `status_code`，FastAPI 默认 200。

- [ ] **Step 2: 跑专用测试确认通过**

Run: `cd backend && venv/bin/python -m pytest tests/test_rate_limit.py -q`
Expected: PASS（key 函数 3 个 + 429 行为 1 个）

- [ ] **Step 3: 跑全套件确认无串扰**

Run: `cd backend && venv/bin/python -m pytest -q`
Expected: PASS（429 测试在 tearDown 里把 limiter 复位并关闭，不影响其它用例）

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_rate_limit.py
git commit -m "test(backend): 评论限流 429 行为测试（阈值、body、Retry-After）"
```

---

## Task 8: nginx 写操作 IP 限流

**Files:**
- Modify: `deploy/nginx.conf`
- Modify: `nginx.example.conf`

> 两份文件内容一致，做相同改动。

- [ ] **Step 1: 在 server 块之前加 map + zone**

在两份文件**第一个 `server {` 块之前**（文件顶部注释之后）插入：

```nginx
# ==============================================================
# 🚦 写操作限流（仅 POST/PUT/PATCH/DELETE 按 IP 计数；GET 等读请求放过）
#    map 给读请求一个空字符串 key —— nginx 对空 key 不计数，等于跳过限流。
#    放在 http 上下文（sites-enabled 文件顶部即 http 上下文）。
# ==============================================================
map $request_method $api_write_key {
    default "";
    POST    $binary_remote_addr;
    PUT     $binary_remote_addr;
    PATCH   $binary_remote_addr;
    DELETE  $binary_remote_addr;
}
limit_req_zone $api_write_key zone=api_write:10m rate=20r/s;
limit_req_status 429;

```

- [ ] **Step 2: 在 /api/v1/ location 内启用 limit_req**

在两份文件的 `location /api/v1/ {` 块内、`proxy_pass` 那一行之前加：

```nginx
        # 写操作粗挡：突发允许 40，平滑放行；读请求 key 为空不受影响
        limit_req zone=api_write burst=40 nodelay;

```

- [ ] **Step 3: 语法自检（若本机装了 nginx）**

Run: `nginx -t -c <(cat deploy/nginx.conf) 2>&1 | head` （或在部署机上 `nginx -t`）
Expected: 若本机无 nginx 或无完整上下文则跳过——示例文件仅落盘，真正校验在部署机 `nginx -t && systemctl reload nginx`。
> 不阻塞：该文件不在 CI，属手动部署物。

- [ ] **Step 4: Commit**

```bash
git add deploy/nginx.conf nginx.example.conf
git commit -m "feat(nginx): 写操作按 IP 限流（map 放过读请求）"
```

---

## Task 9: 前端抽出共享主题

**Files:**
- Create: `frontend/src/theme.ts`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 新建 theme.ts**

创建 `frontend/src/theme.ts`，把 `App.vue` 里的 `themeOverrides` 原样搬过来并导出：

```ts
import type { GlobalThemeOverrides } from 'naive-ui'

export const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#f1f1f1',
    primaryColorHover: '#ffffff',
    primaryColorPressed: '#d8d8d8',
    primaryColorSuppl: '#f1f1f1',
    infoColor: '#d6dce1',
    successColor: '#8dc9a8',
    warningColor: '#d7c986',
    errorColor: '#d28f8f',
    bodyColor: '#060606',
    cardColor: '#101010',
    modalColor: '#101010',
    popoverColor: '#101010',
    tableColor: '#101010',
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderColorHover: 'rgba(255, 255, 255, 0.18)',
    textColorBase: '#f4f4f4',
    textColor1: '#f4f4f4',
    textColor2: '#c8c8c8',
    textColor3: '#9f9f9f',
    placeholderColor: '#676767',
    borderRadius: '4px',
    fontFamily: '"IBM Plex Sans", "Segoe UI", "PingFang SC", sans-serif',
    fontFamilyMono: '"IBM Plex Mono", "SFMono-Regular", monospace',
  },
  Button: {
    borderRadiusTiny: '2px',
    borderRadiusSmall: '4px',
    borderRadiusMedium: '4px',
    borderRadiusLarge: '4px',
    textColorPrimary: '#050505',
    textColorHoverPrimary: '#050505',
    textColorPressedPrimary: '#050505',
    colorHoverPrimary: '#ffffff',
    colorPressedPrimary: '#d7d7d7',
    borderPrimary: '1px solid rgba(255, 255, 255, 0.16)',
    borderHoverPrimary: '1px solid rgba(255, 255, 255, 0.28)',
    borderPressedPrimary: '1px solid rgba(255, 255, 255, 0.3)',
  },
  Card: {
    color: '#101010',
    colorModal: '#101010',
    borderRadius: '8px',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    titleTextColor: '#f4f4f4',
    textColor: '#c8c8c8',
  },
  Input: {
    color: '#0b0b0b',
    colorFocus: '#0b0b0b',
    colorDisabled: '#121212',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderHover: '1px solid rgba(255, 255, 255, 0.22)',
    borderFocus: '1px solid rgba(255, 255, 255, 0.28)',
    borderRadius: '4px',
    textColor: '#f4f4f4',
    placeholderColor: '#656565',
  },
  Layout: {
    color: 'transparent',
    siderColor: '#080808',
    headerColor: '#080808',
    footerColor: '#080808',
  },
}
```

- [ ] **Step 2: App.vue 改为 import**

把 `frontend/src/App.vue` 的 `<script setup>` 里整段 `const themeOverrides = {...}` 删除，改为顶部 import：

```ts
import { NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider } from 'naive-ui'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import { themeOverrides } from '@/theme'
```

模板不变（仍 `:theme-overrides="themeOverrides"`）。

- [ ] **Step 3: 类型检查**

Run: `cd frontend && npx vue-tsc --build --force`
Expected: 无错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/theme.ts frontend/src/App.vue
git commit -m "refactor(frontend): 抽出共享 themeOverrides 到 theme.ts"
```

---

## Task 10: 前端 429 提示

**Files:**
- Create: `frontend/src/services/notify.ts`
- Modify: `frontend/src/services/http.ts`

- [ ] **Step 1: 新建 notify.ts**

创建 `frontend/src/services/notify.ts`：

```ts
import { createDiscreteApi, darkTheme } from 'naive-ui'
import { themeOverrides } from '@/theme'

// 拦截器在 Vue setup 之外，拿不到 useMessage()，用 discrete API。
// 复用暗色主题保持黑白风格一致。
const { message } = createDiscreteApi(['message'], {
  configProviderProps: {
    theme: darkTheme,
    themeOverrides,
  },
})

let lastShownAt = 0

/** 429 限流提示：3 秒内去重，避免狂点时 toast 堆叠。 */
export function notifyRateLimited(detail?: string): void {
  const now = Date.now()
  if (now - lastShownAt < 3000) return
  lastShownAt = now
  message.warning(detail || '操作过于频繁，请稍后再试')
}
```

- [ ] **Step 2: http.ts 加 429 分支**

在 `frontend/src/services/http.ts` 顶部 import 区加：

```ts
import { notifyRateLimited } from '@/services/notify'
```

把响应拦截器的错误回调改为（在 401 分支后加 429 分支）：

```ts
  (error: AxiosError) => {
    // 401 未授权 - 清除登录状态
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
    }
    // 429 限流 - 全局提示（不吞错误，调用方错误态照常触发）
    if (error.response?.status === 429) {
      const detail = (error.response.data as { detail?: string } | undefined)?.detail
      notifyRateLimited(detail)
    }
    return Promise.reject(error)
  }
```

- [ ] **Step 3: 类型检查 + 构建**

Run: `cd frontend && npx vue-tsc --build --force && npm run build-only`
Expected: 类型无错误；构建成功

- [ ] **Step 4: Commit**

```bash
git add frontend/src/services/notify.ts frontend/src/services/http.ts
git commit -m "feat(frontend): 429 限流全局提示（discrete message + 去重）"
```

---

## Task 11: 文档更新

**Files:**
- Modify: `docs/changelog.md`
- Modify: `docs/followups.md`

- [ ] **Step 1: changelog 追加条目**

在 `docs/changelog.md` 顶部加一条 `2026-06-03 限流` 记录：做了什么（nginx 写操作 IP 限流 + slowapi like/comment 按用户、sso 按 IP + 前端 429 提示）+ 为什么（followups §3.1 安全护栏，挡刷赞/灌评论/暴力换码）。

- [ ] **Step 2: followups 标记 §3.1 完成**

在 `docs/followups.md` §3.1 标题后加 `✅ 已完成（2026-06-03）` 并简述落地范围与未做项（不限建节点/上传、未引入 Redis、多 worker 时需换共享存储），与 §1.1 同样的「保留为历史背景」风格。

- [ ] **Step 3: Commit**

```bash
git add docs/changelog.md docs/followups.md
git commit -m "docs: 记录限流改造（changelog + followups §3.1 收口）"
```

---

## 最终验证门槛

- [ ] 后端全绿：`cd backend && venv/bin/python -m pytest -q`
- [ ] 前端类型+构建：`cd frontend && npx vue-tsc --build --force && npm run build-only`
- [ ] `git status` 干净；`git log --oneline main..HEAD` 为本次任务的提交序列

## 审阅与合并（按 CLAUDE.md §3.5）

- [ ] 派 reviewer 子代理审 `git diff main..HEAD`，自跑两套件复核，修掉 Critical/Important
- [ ] 合并前确认 `git status` 干净、`git log --oneline origin/main..HEAD` 清楚
- [ ] **仅在用户明确要求后** `git checkout main && git merge --ff-only feat/rate-limiting && git push origin main`
- [ ] 推送后 `git branch -d feat/rate-limiting`
