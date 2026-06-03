# 限流（Rate Limiting）设计 — 2026-06-03

> 来源：`docs/followups.md` §3.1（重要级安全护栏）。目标：挡住任何登录用户每秒几十次刷
> `POST /interaction/node/{id}/like` 切赞、灌 `POST /interaction/node/{id}/comment` 的滥用，
> 并在网络边缘粗挡裸洪水。

## 决策摘要（用户确认）

- **存储后端**：slowapi 内存（单进程，无 Redis）。多 worker/多实例时再换，已在 followups 备注。
- **应用层覆盖**：点赞 + 评论（按用户）、SSO 换登录态（按 IP）。**不**限建节点/上传。
- **网络层（nginx）**：仅写操作（POST/PUT/PATCH/DELETE）按 IP 粗挡，放过读请求。写示例配置文件，手动部署。
- **前端**：捕获 429，弹一个与暗色主题一致的全局提示（去重，避免狂刷时堆叠）。

## 架构

```
请求 → [nginx: 写操作按 IP 粗挡]            → [FastAPI slowapi: 按用户/IP 细挡]    → 端点
        map 仅 POST/PUT/PATCH/DELETE          like     60/min · user
        zone=api_write rate=20r/s burst=40    comment   6/min · user
        读请求 key 为空 → 跳过                 sso/exchange 10/min · IP
```

两层互补：nginx 在请求进 Python 前挡裸洪水（便宜、抗 DoS，但分不清用户）；slowapi 按登录用户精确挡刷赞/灌评论。429 在两层语义一致。

## 应用层（slowapi）

### 1. 依赖与配置
- `backend/requirements.txt`：加 `slowapi>=0.1.9`。
- `backend/app/core/config.py`：加 `RATE_LIMIT_ENABLED: bool = True`（env 可覆盖；测试用来关）。

### 2. 新模块 `backend/app/core/rate_limit.py`（限流策略集中处，单一职责）
- `get_client_ip(request) -> str`：读 `X-Forwarded-For` 首跳 → `X-Real-IP` → `request.client.host`。
  **关键**：后端在 nginx 后面，不取转发头则所有 IP 都是 `127.0.0.1`，IP 限流形同虚设。
- `user_or_ip_key(request) -> str`：有 `request.state.rate_limit_user_id` 用 `f"user:{id}"`，否则回退 `get_client_ip`。
- `limiter = Limiter(key_func=user_or_ip_key, enabled=settings.RATE_LIMIT_ENABLED)`。
- 阈值常量：`LIKE_LIMIT="60/minute"`、`COMMENT_LIMIT="6/minute"`、`SSO_LIMIT="10/minute"`。

### 3. `backend/main.py` 接线
- `app.state.limiter = limiter`。
- 注册 `RateLimitExceeded` 异常处理器：返回 `429` + body `{"detail": "操作过于频繁，请稍后再试"}` + `Retry-After` 头
  （与全站 `{"detail": ...}` 形状一致；不用 slowapi 默认的 `{"error": ...}`）。
- 用 **per-route 装饰器**，不挂全局 `SlowAPIMiddleware`（无全站默认限额，更干净）。

### 4. `backend/app/api/deps.py`：把用户身份放到 `request.state`
- `get_current_user` 加 `request: Request` 形参；解析出 `user` 后 `request.state.rate_limit_user_id = user.id`。
- 时序：slowapi 装饰器在 FastAPI 解析完依赖后才求值 key_func，所以此时 `request.state` 已写好，按用户计数成立。

### 5. 装饰端点（每个需加 `request: Request` 形参——slowapi 硬性要求）
- `interaction.toggle_node_like` → `@limiter.limit(LIKE_LIMIT)`（默认 key = 按用户）。
- `interaction.create_node_comment` → `@limiter.limit(COMMENT_LIMIT)`（按用户）。
- `auth.exchange_sso_login` → `@limiter.limit(SSO_LIMIT, key_func=get_client_ip)`（未登录，强制按 IP）。

## 网络层（nginx，仅写操作）

`deploy/nginx.conf` 与 `nginx.example.conf` 两份都加，带注释说明需手动 `nginx -t && systemctl reload nginx`：

```nginx
# —— http 上下文（在 server { 之前；sites-enabled 文件顶部即 http 上下文）——
# 只对写方法计数：GET 等读请求 key 为空字符串 → nginx 直接跳过限流，不误伤翻页/轮询
map $request_method $api_write_key {
    default "";
    POST    $binary_remote_addr;
    PUT     $binary_remote_addr;
    PATCH   $binary_remote_addr;
    DELETE  $binary_remote_addr;
}
limit_req_zone $api_write_key zone=api_write:10m rate=20r/s;
limit_req_status 429;

# —— location /api/v1/ 内 ——
limit_req zone=api_write burst=40 nodelay;
```

`map` 是 nginx「只限写、放过读」的惯用法：空字符串 key 不被 `limit_req` 计数。

## 前端 429 提示

拦截器在 Vue setup 外，拿不到 `useMessage()`，故用 `createDiscreteApi` 并复用 App.vue 的暗色主题，保持黑白风格一致。

### 1. 抽出共享主题 `frontend/src/theme.ts`
- 把 `App.vue` 里的 `themeOverrides` 移到 `theme.ts` 导出；`App.vue` 改为 import（消除重复定义，给 discrete API 复用）。

### 2. `frontend/src/services/notify.ts`
- 懒初始化 `createDiscreteApi(['message'], { configProviderProps: { theme: darkTheme, themeOverrides } })`。
- 导出 `notifyRateLimited(detail?: string)`：去重——距上次提示 < 3s 则跳过，避免狂点时 toast 堆叠。

### 3. `frontend/src/services/http.ts` 响应拦截器
- 在现有 401 分支旁加 429 分支：`if (error.response?.status === 429) notifyRateLimited(error.response.data?.detail)`。
- 仍 `return Promise.reject(error)`，让各 mutation 的错误态照常触发（不吞错误）。

## 测试

### 现有测试不被误伤（关键）
- `backend/tests/test_support.py` **模块级** `limiter.enabled = False`（所有测试模块都 import 它）。
- slowapi 在 `enabled=False` 时直接短路、不触碰 `request.app.state`，所以即便 mock 测试直接调被装饰的端点函数也安全；也不会跨用例累积内存计数。

### 专用测试 `backend/tests/test_rate_limit.py`
- setUp：`limiter.enabled = True; limiter.reset()`；tearDown：`limiter.reset(); limiter.enabled = False`。
- 用例：同一用户连发评论，前 6 条 `2xx`、第 7 条断言 `429` + body `detail` + `Retry-After` 头存在。
- 选取评论（6/min）而非点赞（60/min）做断言，触发阈值成本低。

## 验证门槛
- 后端：`cd backend && venv/bin/python -m pytest -q`（含新 `test_rate_limit.py`，全绿）。
- 前端：`cd frontend && npx vue-tsc --build --force && npm run build-only`。
- nginx：示例配置仅落盘，部署侧 `nginx -t` 自检（不在本仓库 CI）。

## 范围外（按用户选择）
- 不限建节点 / 上传。
- 不引入 Redis（内存够用；多 worker 时再换）。
- 时间衰减热度、排行榜等其余 followups 项不在本次。
