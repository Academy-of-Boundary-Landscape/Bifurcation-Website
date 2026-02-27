# API v1 接口总结（基于 `backend/app/api/v1` 源码）

> 目的：给自己快速回顾「有哪些接口、做什么、怎么调」。

## 1. 全局信息

- 全局前缀：`/api/v1`（来自 `app/core/config.py` 的 `API_V1_STR`）
- 路由挂载（`app/api/api.py`）：
  - `/auth`
  - `/story`
  - `/users`
  - `/interaction`
  - `/admin`
  - `/discovery`
  - `/uploads`

---

## 2. 鉴权规则速记

- Bearer Token 登录入口：`/api/v1/auth/login`（OAuth2PasswordBearer）
- 常用依赖：
  - `get_current_active_user`：需要登录且用户 `is_active=True`
  - `get_current_admin`：需要管理员角色
  - `get_current_user_or_none`：可匿名访问；有 token 但无效/未激活/未验证会当作游客

---

## 3. Auth 模块（`/api/v1/auth`）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| POST | `/send-code-for-activation` | 发送注册激活验证码 | 否 | `email` | `detail` |
| POST | `/verify-email-for-activation` | 验证注册验证码并激活账号 | 否 | `email`, `code` | `detail` |
| POST | `/register` | 注册用户 | 否 | `username`, `email`, `password` | 用户基础信息 |
| POST | `/login` | 登录获取 JWT（支持邮箱或用户名） | 否 | 表单：`username`(邮箱/用户名), `password` | `access_token`, `token_type` |
| GET | `/me` | 获取当前登录用户资料+统计 | 是（active） | - | 用户画像（含节点数/获赞数） |
| PATCH | `/me` | 修改个人资料 | 是（active） | `username?`, `bio?`, `avatar?` | 用户信息 |
| POST | `/send-code-for-password-reset` | 发送重置密码验证码 | 否 | `email` | `detail` |
| POST | `/change-password` | 登录态修改密码 | 是（active） | `old_password`, `new_password` | `detail` |
| POST | `/reset-password` | 验证码重置密码 | 否 | `email`, `code`, `new_password` | `detail` |

---

## 4. Users 模块（`/api/v1/users`）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| GET | `/{user_id}` | 公开查看他人主页 | 否 | path: `user_id>=1` | 用户画像（含节点数、获赞总数） |

---

## 5. Story 模块（`/api/v1/story`）

### 5.1 活动/故事集（Book）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| POST | `/books` | 创建活动 | 管理员 | `StoryBookCreate`（title/phase/时间窗口等） | `StoryBookResponse` |
| PATCH | `/books/{book_id}` | 更新活动 | 管理员 | path:`book_id`, body:`StoryBookUpdate` | `StoryBookResponse` |
| GET | `/books` | 活动列表 | 否 | `phase?`, `skip`, `limit` | `StoryBookResponse[]` |
| GET | `/books/{book_id}` | 活动详情 | 否 | path:`book_id` | `StoryBookResponse` |

### 5.2 节点（Node）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| GET | `/tree` | 获取某活动故事树 | 可匿名（可选登录） | `book_id` | `StoryNodeTreeItem[]` |
| GET | `/node/{node_id}/path` | 获取节点阅读路径（从根到当前） | 可匿名（可选登录） | path:`node_id` | `StoryNodeRead[]` |
| POST | `/node` | 提交续写（普通用户默认 pending） | 登录且 active | `StoryNodeCreate` | `StoryNodeListItem` |
| GET | `/node/{node_id}` | 查看节点详情正文 | 可匿名（可选登录，带可见性控制） | path:`node_id` | `StoryNodeRead` |
| GET | `/user/{user_id}/nodes` | 用户创作列表 | 可匿名（可选登录） | path:`user_id`, `status?`, `skip`, `limit` | `StoryNodeListItem[]` |
| PATCH | `/node/{node_id}` | 修改节点 | 登录且 active（作者或管理员） | path:`node_id`, body:`NodeUpdate` | `StoryNodeRead` |
| DELETE | `/node/{node_id}` | 软删除节点（改 archived） | 登录且 active（作者或管理员） | path:`node_id` | `detail` |

---

## 6. Interaction 模块（`/api/v1/interaction`）

### 6.1 点赞

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| POST | `/node/{node_id}/like` | 点赞/取消点赞（toggle） | 登录且 active | path:`node_id` | `status`, `action`, `likes_count` |

### 6.2 评论

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| GET | `/node/{node_id}/comments` | 评论列表 | 否 | path:`node_id`, `skip`, `limit` | `CommentResponse[]` |
| POST | `/node/{node_id}/comment` | 发表评论 | 登录且 active | path:`node_id`, body:`content` | `CommentResponse` |

### 6.3 通知

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| GET | `/notifications` | 我的通知列表 | 登录且 active | `skip`, `limit` | `NotificationResponse[]` |
| GET | `/notifications/unread-count` | 我的未读通知数 | 登录且 active | - | `unread_count` |
| PUT | `/notifications/{notification_id}/read` | 单条通知标记已读 | 登录且 active | path:`notification_id` | `detail` |
| PUT | `/notifications/read` | 全部通知标记已读 | 登录且 active | - | `detail` |

---

## 7. Discovery 模块（`/api/v1/discovery`）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| GET | `/feed` | 最新动态（瀑布流） | 否 | `book_id?`, `skip`, `limit` | `StoryNodeListItem[]` |
| GET | `/trending` | 热门分支榜（近 N 天，冷启动有兜底） | 否 | `days(1-30)`, `limit` | `StoryNodeListItem[]` |
| GET | `/search` | 关键词搜索（标题/内容） | 否 | `q`, `limit` | `StoryNodeListItem[]` |

---

## 8. Admin 模块（`/api/v1/admin`）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| GET | `/nodes/pending` | 待审核节点列表 | 管理员 | `skip`, `limit` | `StoryNodeTreeItem[]` |
| PATCH | `/nodes/{node_id}/audit` | 审核/强制改节点状态 | 管理员 | path:`node_id`, body:`status`,`reject_reason?` | `StoryNodeTreeItem` |
| GET | `/users` | 用户列表（筛选+分页） | 管理员 | `skip`,`limit`,`role?`,`is_active?`,`keyword?` | `UserResponse[]` |
| GET | `/stats` | 仪表盘统计 | 管理员 | - | 用户/节点统计对象 |
| PATCH | `/users/{user_id}` | 强制改用户信息/封禁 | 管理员 | path:`user_id`, body:`UserAdminUpdate` | `UserResponse` |

---

## 9. Upload 模块（`/api/v1/uploads`）

| 方法 | 路径 | 说明 | 鉴权 | 关键入参 | 主要返回 |
|---|---|---|---|---|---|
| POST | `/` | 上传图片并返回 URL | 登录且 active | multipart: `file`（仅图片，<=5MB，白名单后缀） | `url` |

静态访问路径示例：返回 `/static/uploads/xxx.jpg`，由 `main.py` 挂载静态目录。

---

## 10. 个人使用建议（便于自测）

1. 先走注册/激活/登录：
   - `POST /api/v1/auth/register`
   - `POST /api/v1/auth/send-code-for-activation`
   - `POST /api/v1/auth/verify-email-for-activation`
   - `POST /api/v1/auth/login`
2. 带 `Authorization: Bearer <token>` 测试需要登录的接口。
3. 普通用户与管理员用不同 token 测试权限差异（尤其 `/admin/*`、`/story/node` 根节点创建）。
