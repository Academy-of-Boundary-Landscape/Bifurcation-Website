# 后端 API 完整参考（源码核对版）

> 本文档逐行核对 `backend/app/api/v1/*.py`、`api.py`、`deps.py`、`schemas/*.py`、`main.py` 生成（2026-06-02 重写，取代旧版）。
> 配套审阅见 `docs/backend-review/`（前端需求对比、核心正确性、协同优化方案）。
> 所有路径均含全局前缀 `/api/v1`（`config.py:44` `API_V1_STR = "/api/v1"`，`main.py:66` 挂载）。

## 0. 全局事实

- FastAPI app 在 `backend/main.py:14`（注意：`app/main.py` 只是 `from main import app` 的转发桩，真正入口是仓库 `backend/main.py`）。
- 全局前缀：`/api/v1`（`main.py:66`）。
- 子路由前缀（`api.py:8-22`）：
  - `auth.router` → `/auth`
  - `story.router` → `/story`
  - `users.router` → `/users`
  - `interaction.router` → `/interaction`
  - `admin.router` → `/admin`
  - `discovery.router` → `/discovery`
  - `upload.router` → `/uploads`
- 前缀外的额外端点：
  - `GET /health`（`main.py:51`，无认证，返回 `{"status":"ok","service":...}`）
  - 静态资源挂载 `/static`（`main.py:60`，`StaticFiles`）

### 鉴权依赖（`deps.py`）

| 依赖 | 行为 | 失败结果 |
| --- | --- | --- |
| `get_current_user` (`deps.py:18`) | 必须带合法本站 JWT | 401 |
| `get_current_active_user` (`deps.py:47`) | 已登录且 `is_active=True` | 401 / 400「用户已被封禁」 |
| `get_current_admin` (`deps.py:81`) | 已登录 active 且 `role==ADMIN` | 403 |
| `get_current_user_or_none` (`deps.py:54`) | 可选登录；无 token / 无效 / 已封禁 → 返回 `None`（按游客） | 不报错 |

> 认证语义术语：**public**=无依赖；**authed**=`get_current_active_user`；**admin**=`get_current_admin`；**optional**=`get_current_user_or_none`。

### 核心响应 Schema 字段速查

- **`StoryNodeListItem`**（`schemas/story.py:41`，列表/轻量，**无 content**）字段：
  `id, parent_id, root_id, book_id, author{AuthorInfo: id,username,avatar}, title, summary, branch_name, status, visibility, zone, word_count, likes_count, comments_count, children_count, is_ending, freeze_interactions, is_featured, feature_rank, published_at, created_at, updated_at`
- **`StoryNodeRead`**（`schemas/story.py:75`，继承 ListItem，**含正文**）额外字段：
  `content, reject_reason, archived_reason, reviewed_by, reviewed_at, is_liked(默认 False)`
- **`StoryNodeTreeItem`**（`schemas/story.py:86`，继承 ListItem）额外字段：`children: List[StoryNodeTreeItem]`
- **`StoryBookResponse`**（`schemas/story_book.py:32`）：`id, title, description, cover_image, phase, start_at, writing_end_at, showcase_end_at, allow_new_nodes, created_at`
- **`UserResponse`**（`schemas/user.py:11`）：`id, email, username, display_name, role, is_active, bio, avatar, created_at, updated_at`
- **`UserProfileResponse`**（`schemas/user.py:27`，继承 UserResponse）额外：`nodes_count(默认0), likes_count(默认0)`
- **`CommentResponse`**（`schemas/interaction.py:23`）：`id, node_id, book_id, content, created_at, deleted_at, user(AuthorInfo|None)`
- **`NotificationResponse`**（`schemas/interaction.py:36`）：`id, type, sender(AuthorInfo|None), node_id, comment_id, message, is_read, created_at`
- **`LikeToggleResponse`**（`schemas/interaction.py:11`）：`status, action, likes_count`（service 返回值见 `services/interactions.py:61-64`）
- **`NotificationUnreadCountResponse`**（`schemas/interaction.py:49`）：`unread_count`
- **`MessageResponse`**（`schemas/story.py:12` 与 `common.py:18`）：`detail`
- **`SSOLoginUrlResponse`**（`schemas/sso.py:4`）：`authorize_url, state`
- **`SSOExchangeResponse`**（`schemas/sso.py:14`）：`access_token, token_type, redirect_to, is_new_user`

> 注意：`StoryBookListResponse`（`story_book.py:49`，含 `books:[]`）**未被任何端点使用**——`GET /story/books` 返回的是裸 `List[StoryBookResponse]`。

---

## 1. Auth 模块（`auth.py`，前缀 `/auth`）

| # | 方法 + 路径 | 认证 | 参数 | response_model（裸 list?） | 行为 |
| --- | --- | --- | --- | --- | --- |
| 1 | `GET /api/v1/auth/sso/login-url` (`auth.py:20`) | public | query `redirect_to: str = "/books"` | `SSOLoginUrlResponse`（对象） | 生成 Casdoor 登录跳转地址与签名 state |
| 2 | `POST /api/v1/auth/sso/exchange` (`auth.py:31`) | public | body `SSOExchangeRequest{code, state}` | `SSOExchangeResponse`（对象） | 用 Casdoor code 换本站 JWT |
| 3 | `GET /api/v1/auth/me` (`auth.py:54`) | authed | — | `UserProfileResponse`（对象） | 当前用户资料 + 实时统计 `nodes_count`(该用户所有节点) / `likes_count`(收到的赞) |
| 4 | `PATCH /api/v1/auth/me` (`auth.py:99`) | authed | body `UserUpdate{username?, bio?, avatar?}` | `UserResponse`（对象） | 改个人资料（`exclude_unset`） |

> 细节：`GET /auth/me` 的 `nodes_count` 统计 **作者全部节点**（不限状态，`auth.py:70-74`），与 `GET /users/{id}` 的「仅 published」口径不同——见下。

---

## 2. Story 模块（`story.py`，前缀 `/story`）

| # | 方法 + 路径 | 认证 | 参数（含默认/上限） | response_model（裸 list?） | 行为 |
| --- | --- | --- | --- | --- | --- |
| 5 | `POST /api/v1/story/books` (`story.py:97`) | admin | body `StoryBookCreate` | `StoryBookResponse`（对象） | 创建活动 |
| 6 | `PATCH /api/v1/story/books/{book_id}` (`story.py:128`) | admin | path `book_id≥1`; body `StoryBookUpdate` | `StoryBookResponse`（对象） | 更新活动 |
| 7 | `GET /api/v1/story/books` (`story.py:156`) | public | query `phase?`; `skip=0(≥0)`; `limit=100(1..200)` | **`List[StoryBookResponse]`（裸 list，无 total）** | 活动列表，无 phase 时排除 archived |
| 8 | `GET /api/v1/story/books/{book_id}` (`story.py:184`) | public | path `book_id≥1` | `StoryBookResponse`（对象） | 活动详情，404 不存在 |
| 9 | `GET /api/v1/story/tree` (`story.py:208`) | optional | query `book_id≥1`（必填） | **`List[StoryNodeTreeItem]`（裸 list，嵌套树，无 total）** | 整棵故事树；按可见性过滤；不返回正文 |
| 10 | `GET /api/v1/story/node/{node_id}/lineage` (`story.py:266`) | optional | path `node_id≥1` | **`List[StoryNodeRead]`（裸 list）** | 根→当前节点路径（与 path 同一函数） |
| 11 | `GET /api/v1/story/node/{node_id}/path` (`story.py:276`) | optional | path `node_id≥1` | **`List[StoryNodeRead]`（裸 list）** | 同上（别名路由，`get_node_reading_path`） |
| 12 | `POST /api/v1/story/node` (`story.py:351`) | authed | body `StoryNodeCreate{book_id,parent_id?,title?,content(≥10),branch_name?,summary?,zone}` | `StoryNodeListItem`（对象） | 提交续写（走 service `create_story_node_record`） |
| 13 | `GET /api/v1/story/node` (`story.py:372`) | optional | query `parent_id≥1`（必填）; `skip=0(≥0)`; `limit=20(1..100)` | **`List[StoryNodeListItem]`（裸 list，无 total）** | 某节点的直接子分支 |
| 14 | `GET /api/v1/story/node/{node_id}` (`story.py:402`) | optional | path `node_id≥1` | `StoryNodeRead`（对象，含 `is_liked`） | 节点正文详情；403/404 按可见性 |
| 15 | `GET /api/v1/story/user/{user_id}/nodes` (`story.py:449`) | optional | path `user_id≥1`; query `status?`; `skip=0(≥0)`; `limit=50(1..200)` | **`List[StoryNodeListItem]`（裸 list，无 total）** | 用户创作列表（本人/admin 可看全部状态，他人仅 published） |
| 16 | `PATCH /api/v1/story/node/{node_id}` (`story.py:486`) | authed | path `node_id≥1`; body `NodeUpdate{title?,content?,branch_name?,summary?}` | `StoryNodeRead`（对象） | 改节点（已发布节点普通用户禁改正文类字段） |
| 17 | `DELETE /api/v1/story/node/{node_id}` (`story.py:541`) | authed | path `node_id≥1` | `MessageResponse{detail}`（对象） | 软删除（置 archived，回收父 children_count） |

---

## 3. Users 模块（`users.py`，前缀 `/users`）

| # | 方法 + 路径 | 认证 | 参数 | response_model | 行为 |
| --- | --- | --- | --- | --- | --- |
| 18 | `GET /api/v1/users/{user_id}` (`users.py:15`) | public | path `user_id≥1` | `UserProfileResponse`（对象） | 公开主页；`nodes_count`/`likes_count` 均 **仅统计 published 节点**（`users.py:40-55`） |

---

## 4. Interaction 模块（`interaction.py`，前缀 `/interaction`）

| # | 方法 + 路径 | 认证 | 参数（含默认/上限） | response_model（裸 list?） | 行为 |
| --- | --- | --- | --- | --- | --- |
| 19 | `POST /api/v1/interaction/node/{node_id}/like` (`interaction.py:26`) | authed | path `node_id` | `LikeToggleResponse{status,action,likes_count}`（对象） | 点赞 toggle；返回最新 likes_count |
| 20 | `GET /api/v1/interaction/node/{node_id}/comments` (`interaction.py:50`) | public | path `node_id`; `skip=0(≥0)`; `limit=50(1..100)` | **`List[CommentResponse]`（裸 list，无 total）** | 评论列表（过滤软删除） |
| 21 | `POST /api/v1/interaction/node/{node_id}/comment` (`interaction.py:79`) | authed | path `node_id`; body `CommentCreate{content}` | `CommentResponse`（对象） | 发表评论 |
| 22 | `GET /api/v1/interaction/notifications` (`interaction.py:109`) | authed | `skip=0(≥0)`; `limit=50(1..100)` | **`List[NotificationResponse]`（裸 list，无 total）** | 我的通知列表 |
| 23 | `GET /api/v1/interaction/notifications/unread-count` (`interaction.py:138`) | authed | — | `NotificationUnreadCountResponse{unread_count}`（对象） | 未读计数（**唯一直接给计数的列表相关端点**） |
| 24 | `PUT /api/v1/interaction/notifications/{notification_id}/read` (`interaction.py:162`) | authed | path `notification_id` | `MessageResponse{detail}`（对象） | 单条已读 |
| 25 | `PUT /api/v1/interaction/notifications/read` (`interaction.py:191`) | authed | — | `MessageResponse{detail}`（对象） | 一键全部已读 |
| 26 | `DELETE /api/v1/interaction/comment/{comment_id}` (`interaction.py:220`) | authed | path `comment_id` | `MessageResponse{detail}`（对象） | 软删除评论（同步回收节点 comments_count） |

---

## 5. Discovery 模块（`discovery.py`，前缀 `/discovery`）

| # | 方法 + 路径 | 认证 | 参数（含默认/上限） | response_model（裸 list?） | 行为 |
| --- | --- | --- | --- | --- | --- |
| 27 | `GET /api/v1/discovery/featured` (`discovery.py:20`) | public | `limit=6(1..50)` | **`List[StoryNodeListItem]`（裸 list，无 total/skip）** | 精选节点（is_featured + feature_rank 排序）。**旧文档完全遗漏此端点** |
| 28 | `GET /api/v1/discovery/feed` (`discovery.py:62`) | public | `book_id?(≥1)`; `skip=0(≥0)`; `limit=20(1..100)` | **`List[StoryNodeListItem]`（裸 list，无 total）** | 最新动态瀑布流 |
| 29 | `GET /api/v1/discovery/trending` (`discovery.py:101`) | public | `days=7(1..30)`; `limit=10(1..50)` | **`List[StoryNodeListItem]`（裸 list，无 total/skip）** | 近 N 天热门，按 likes_count；不足 3 条回退历史总榜 |
| 30 | `GET /api/v1/discovery/search` (`discovery.py:154`) | public | `q`(必填,1..50); `limit=20(1..100)` | **`List[StoryNodeListItem]`（裸 list，无 total/skip）** | 标题/正文模糊搜索 published |

---

## 6. Admin 模块（`admin.py`，前缀 `/admin`，全部 admin 认证）

| # | 方法 + 路径 | 参数（含默认/上限） | response_model（裸 list?） | 行为 |
| --- | --- | --- | --- | --- |
| 31 | `GET /api/v1/admin/nodes` (`admin.py:27`) | `skip=0(≥0)`; `limit=50(1..200)`; `status?`; `book_id?(≥1)`; `author_id?(≥1)`; `keyword?(1..80)` | **`List[StoryNodeRead]`（裸 list，无 total）** | 节点管理列表（多条件筛选） |
| 32 | `GET /api/v1/admin/nodes/pending` (`admin.py:77`) | `skip=0(≥0)`; `limit=50(1..200)` | **`List[StoryNodeRead]`（裸 list，无 total）** | 待审核工作台（按时间正序） |
| 33 | `PATCH /api/v1/admin/nodes/{node_id}/audit` (`admin.py:109`) | path `node_id`; body `NodeAuditRequest{status,reject_reason?}` | `StoryNodeRead`（对象） | 审核/强改节点状态（走 service） |
| 34 | `PATCH /api/v1/admin/users/{user_id}` (`admin.py:139`) | path `user_id`; body `UserAdminUpdate{role?,is_active?,username?,bio?,avatar?}` | `UserResponse`（对象） | 强改用户信息/封禁 |
| 35 | `GET /api/v1/admin/users` (`admin.py:183`) | `skip=0(≥0)`; `limit=50(1..200)`; `role?`; `is_active?`; `keyword?(1..50)` | **`List[UserResponse]`（裸 list，无 total）** | 用户列表（多条件筛选） |
| 36 | `GET /api/v1/admin/stats` (`admin.py:224`) | — | **无 response_model**（裸 dict） | 仪表盘聚合，结构见下 |

`GET /admin/stats` 返回（`admin.py:261-275`）：
```json
{
  "users": {"total": N, "active": N, "inactive": N, "new_7d": N},
  "nodes": {"total": N, "pending": N, "published": N, "archived": N, "new_7d": N}
}
```

---

## 7. Uploads 模块（`upload.py`，前缀 `/uploads`）

| # | 方法 + 路径 | 认证 | 参数 | response_model | 行为 |
| --- | --- | --- | --- | --- | --- |
| 37 | `POST /api/v1/uploads/` (`upload.py:24`) | authed | multipart `file: UploadFile` | `UploadResponse{url}`（对象，定义在 `upload.py:16`） | 上传图片（MIME=image/\*，≤5MB，后缀白名单），返回 `/static/uploads/<uuid>.<ext>` |

> 注意路径**带尾斜杠** `/uploads/`，不可省略。

---

## 8. 分页与总数缺口（核心问题）

这是前端「指标说谎」的根因：**几乎所有列表端点都返回裸 `List[X]`，没有任何 `total` / `count` / 分页元数据**。客户端无法知道真实总数，只能用「当前页返回条数」冒充总量，或在「拿满 limit 条」时无法判断是否还有下一页。

### 8.1 完全无法获知真实 total 的 list 端点（裸 List，无元数据）

| 端点 | skip | limit（默认/上限） | 能否知道 total |
| --- | --- | --- | --- |
| `GET /story/books` (#7) | ✅ skip | 100 / 200 | ❌ 无 total |
| `GET /story/tree` (#9) | ❌（一次性全量树，按可见性过滤，无分页） | — | ❌ 无 total/无 count |
| `GET /story/node/{id}/lineage`、`/path` (#10/#11) | ❌（路径长度即条数，但语义上是完整链） | — | ❌（链本身完整，但无显式计数字段） |
| `GET /story/node` 子分支 (#13) | ✅ | 20 / 100 | ❌ 无 total（前端不知该节点共有多少子分支，尽管父节点对象上有 `children_count`，见 8.3） |
| `GET /story/user/{id}/nodes` (#15) | ✅ | 50 / 200 | ❌ 无 total |
| `GET /interaction/node/{id}/comments` (#20) | ✅ | 50 / 100 | ❌ 无 total（节点对象上有 `comments_count` 可借用，见 8.3） |
| `GET /interaction/notifications` (#22) | ✅ | 50 / 100 | ❌ 无 total（有独立 unread-count，但**无 total/已读总数**） |
| `GET /discovery/featured` (#27) | ❌ | 6 / 50 | ❌ |
| `GET /discovery/feed` (#28) | ✅ | 20 / 100 | ❌ 无 total |
| `GET /discovery/trending` (#29) | ❌（无 skip） | 10 / 50 | ❌ |
| `GET /discovery/search` (#30) | ❌（无 skip，仅 limit） | 20 / 100 | ❌ 无命中总数 |
| `GET /admin/nodes` (#31) | ✅ | 50 / 200 | ❌ 无 total（**后台分页器无法显示总页数/总条数**） |
| `GET /admin/nodes/pending` (#32) | ✅ | 50 / 200 | ❌ 无 total |
| `GET /admin/users` (#35) | ✅ | 50 / 200 | ❌ 无 total |

**结论：上表 14 个列表端点全部缺失 total。** 没有任何一个返回 `total`/`count` 包裹对象。`StoryBookListResponse` 这类「带容器」的 schema 虽然存在但根本没被使用，且即便用了也只有 `books:[]`、依然没有 `total`。

### 8.2 唯一能直接拿到计数的端点

- `GET /interaction/notifications/unread-count` (#23) → `{unread_count}`：但它只给「未读数」，**不给通知总数**，因此通知列表的分页总数仍然缺失。
- `GET /admin/stats` (#36)：给出全站聚合计数（users/nodes 各维度），可用于仪表盘卡片，但**无法对应任何具体筛选条件下的列表分页**（例如 `admin/nodes?keyword=x` 的命中总数它给不了）。

### 8.3 对象上的去规范化计数（denormalized counts）—— 可作为局部「真值」来源

`StoryNode` 表上物化了以下计数列（`models/story.py:116-118` + `word_count:68`），并通过 `StoryNodeListItem`/`StoryNodeRead` 直接返回，**无需额外请求**：

- `likes_count`（点赞数，toggle 时增减，`services/interactions.py:42-48`）
- `comments_count`（评论数，删评论时回收，`interaction.py:266-272`）
- `children_count`（直接子节点数，删节点时回收，`story.py:586-594`）
- `word_count`（字数）

含义：
- **节点的子分支总数**可从父节点的 `children_count` 得到（即使 `GET /story/node?parent_id=` 分页不带 total，前端仍能用父对象的 `children_count` 显示总数）。
- **节点评论总数**可从节点对象 `comments_count` 得到（`GET .../comments` 自身无 total，但详情对象给了）。
- **节点点赞总数**直接在对象上（`likes_count`）。

需要单独调用 / 无对象计数支撑的场景：
- **books 列表、users 列表、admin nodes 列表、feed/search/trending/featured、notifications 列表** 都没有对应的「容器级总数」，且这些资源本身没有外层 denormalized 总计数 → 前端只能靠 `admin/stats`（仅全站维度）或干脆无法得知。
- 用户维度的 `nodes_count`/`likes_count` 仅在 `GET /auth/me`、`GET /users/{id}` 的 profile 对象里**实时 COUNT 计算**给出（两者口径不同：me=全状态，users=仅 published），其它列表端点不带。

> 风险点（口径不一致，易导致「指标说谎」）：
> - `GET /auth/me` 的 `nodes_count` 含 pending/archived；`GET /users/{id}` 仅 published。同一用户在「我的主页」和「别人看我的主页」上数字会不同。
> - `likes_count` 在 profile 上是「收到的赞」的实时聚合；而节点对象上的 `likes_count` 是单节点物化值。语义不同，勿混用。

---

## 9. 旧文档 `docs/backend/api.md` 的过时/错误点

1. **遗漏 `GET /api/v1/discovery/featured`**（旧文 §4.6 只列了 feed/trending/search，缺精选节点端点 `discovery.py:20`）。
2. **遗漏 `GET /api/v1/auth/me` 与 profile 的统计字段语义**：旧文未说明 `nodes_count`/`likes_count` 注入，也未指出 me（全状态）与 users（仅 published）口径不一致。
3. **未记录任何分页参数与上限**：旧文通篇没有 skip/limit 默认值与 max（这正是 total 缺口问题的关键背景），也未声明所有列表都是裸 List 无 total。
4. **`lineage` 与 `path` 是同一处理函数的双路由别名**（`story.py:266` 和 `:276` 共用 `get_node_reading_path`），旧文把它们列为两个独立条目而未点明二者完全等价。
5. **未提及对象上的 denormalized 计数字段**（likes_count/comments_count/children_count/word_count），导致前端不知道可以从对象拿这些「真值」而误去拼凑。
6. **`/uploads/` 尾斜杠必需**、上传约束（image MIME、5MB、后缀白名单、空文件 400）旧文未写。
7. 旧文 §5.3 称 path/lineage 用 `StoryNodeRead` —— 此点正确；但未说明 `StoryNodeRead.is_liked` 仅在 `GET /node/{id}` 单点详情里真正计算填充，列表/路径接口里恒为默认 `False`。
8. 旧文未指出 `StoryBookListResponse` 这一「带容器」schema 定义了却未被使用，`GET /story/books` 实为裸 List。
