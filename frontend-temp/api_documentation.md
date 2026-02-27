# Tree Story Project 后端 API 文档 (前端交接版)

本文档基于 OpenAPI 3.1.0 规范整理，旨在帮助前端同学快速理解各接口的功能、请求方式、参数及返回数据。

---

## 基本信息

- **项目名称**：Tree Story Project  
- **基础路径**：所有接口以 `/api/v1/` 开头（例如认证接口 `/api/v1/auth/...`）  
- **认证方式**：OAuth2 Password Flow，登录后获取 `access_token`，后续请求需在 **Authorization 头**中携带 `Bearer <token>`。  
  > 注意：`/api/v1/auth/login` 用于获取 token，该接口使用表单格式，其他接口大部分使用 JSON。

---

## 通用数据结构

### 用户简略信息 (AuthorInfo)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户ID |
| username | string | 用户名 |
| avatar | string/null | 头像URL |

### 节点状态 (NodeStatus)
枚举值：`pending`（待审核）、`published`（已发布）、`locked`（已锁定，表示该分支完结）、`rejected`（已拒绝）

### 用户角色 (UserRole)
枚举值：`admin`（管理员）、`writer`（普通写手）、`banned`（小黑屋/封禁）

### 通用响应结构
- **成功响应**：通常直接返回业务数据（如对象、数组）或一个包含 `detail` 的简单消息。
- **错误响应**：大部分返回 JSON 对象，包含 `detail` 字段（字符串或错误详情数组）。  
  对于 422 参数校验错误，会返回 `ValidationErrorResponse`，其中 `detail` 是错误项数组。

---

## 认证模块 (`/auth`)

### 1. 发送邮箱验证码 (用于注册)
- **URL**: `/api/v1/auth/send-code-for-activation`
- **Method**: `POST`
- **功能**: 向指定邮箱发送 6 位验证码（用于激活账号）
- **请求体 (JSON)**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **响应 200**:
  ```json
  { "detail": "验证码发送成功" }
  ```
- **响应 400**: 邮箱已注册并激活
- **响应 422**: 参数校验失败（如邮箱格式错误）

### 2. 验证邮箱验证码 (用于激活)
- **URL**: `/api/v1/auth/verify-email-for-activation`
- **Method**: `POST`
- **功能**: 校验邮箱和验证码是否正确，成功后该邮箱可进入注册流程（注意：该接口本身不创建用户）
- **请求体 (JSON)**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456"
  }
  ```
- **响应 200**: `{ "detail": "验证成功" }`
- **响应 422**: 验证码错误或过期

### 3. 用户注册
- **URL**: `/api/v1/auth/register`
- **Method**: `POST`
- **功能**: 完成注册，创建用户（需先验证邮箱）
- **请求体 (JSON)**:
  ```json
  {
    "email": "user@example.com",
    "username": "myusername",
    "password": "123456"
  }
  ```
- **响应 200** (UserCreateResponse):
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "username": "myusername",
    "role": "writer",
    "is_active": true,
    "is_verified": true
  }
  ```

### 4. 登录 (获取 Token)
- **URL**: `/api/v1/auth/login`
- **Method**: `POST`
- **功能**: 使用用户名或邮箱 + 密码登录，获取 access_token（后续请求需携带）
- **请求体 (表单格式 `application/x-www-form-urlencoded`)**:
  ```
  username: 用户名或邮箱
  password: 密码
  ```
  其他可选字段如 `grant_type` 等可忽略。
- **响应 200**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
  ```

### 5. 获取当前登录用户信息
- **URL**: `/api/v1/auth/me`
- **Method**: `GET`
- **功能**: 获取自己的详细资料（需登录）
- **响应 200** (UserProfileResponse):
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "username": "myusername",
    "role": "writer",
    "is_active": true,
    "is_verified": true,
    "bio": null,
    "avatar": null,
    "nodes_count": 0,
    "likes_count": 0
  }
  ```

### 6. 修改个人资料
- **URL**: `/api/v1/auth/me`
- **Method**: `PATCH`
- **功能**: 更新自己的用户名、简介、头像（需登录）
- **请求体 (JSON)**:
  ```json
  {
    "username": "newname",   // 可选
    "bio": "新简介",          // 可选
    "avatar": "https://..."   // 可选
  }
  ```
- **响应 200**: 更新后的用户信息（同 `UserResponse`）

### 7. 发送重置密码验证码
- **URL**: `/api/v1/auth/send-code-for-password-reset`
- **Method**: `POST`
- **功能**: 忘记密码时，向已注册邮箱发送验证码（需验证邮箱存在）
- **请求体 (JSON)**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456"   // 注意：此接口实际只需 email，文档可能有误，应以实际为准
  }
  ```
  > 根据描述，这里是“验证邮箱并发送重置密码验证码”，可能实际只需 email。建议以后端实际为准。

### 8. 重置密码
- **URL**: `/api/v1/auth/reset-password`
- **Method**: `POST`
- **功能**: 使用验证码设置新密码
- **请求体 (JSON)**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456",
    "new_password": "newpass123"
  }
  ```
- **响应 200**: `{ "detail": "密码重置成功" }`

---

## 用户模块 (`/users`)

### 查看他人主页 (公开)
- **URL**: `/api/v1/users/{user_id}`
- **Method**: `GET`
- **功能**: 查看指定用户的公开资料（无需登录）
- **路径参数**:
  - `user_id`: 用户ID
- **响应 200**: 同 `UserProfileResponse`（包含 nodes_count, likes_count）
- **响应 404**: 用户不存在

---

## 故事活动 (书本) 模块 (`/story/books`)

活动（Book）相当于一个故事树的根容器，管理员可创建多个活动。

### 1. 创建活动 (管理员)
- **URL**: `/api/v1/story/books`
- **Method**: `POST`
- **功能**: 管理员新建一个故事活动（需要 admin 权限）
- **请求体 (JSON)**:
  ```json
  {
    "title": "活动标题",
    "description": "描述",
    "cover_image": "https://..."   // 可选
  }
  ```
- **响应 200**: 创建的 `StoryBookResponse` 对象

### 2. 获取活动列表 (公开)
- **URL**: `/api/v1/story/books`
- **Method**: `GET`
- **功能**: 分页获取所有活动（支持 skip/limit）
- **查询参数**:
  - `skip`: 跳过数量，默认 0
  - `limit`: 返回条数，默认 100，最大 200
- **响应 200**: `StoryBookResponse` 数组

### 3. 更新活动 (管理员)
- **URL**: `/api/v1/story/books/{book_id}`
- **Method**: `PATCH`
- **功能**: 管理员修改活动信息（字段均可选）
- **路径参数**: `book_id`
- **查询参数** (均在 query 中，不是 JSON body):
  - `title`: 新标题
  - `description`: 新描述
  - `cover_image`: 新封面
  - `is_active`: 是否激活（true/false）
- **响应 200**: 更新后的 `StoryBookResponse`

---

## 故事节点模块 (`/story/node` 和 `/story/tree`)

### 故事树相关概念
- 每个节点代表一段续写内容。
- 节点有状态（pending/published/locked/rejected），控制可见性。
- 权限规则：
  - **管理员**：所有节点可见。
  - **普通用户**：已发布(published)/已锁定(locked)的节点 + 自己创作的节点（含 pending/rejected）。
  - **游客**：仅可见 published/locked 的节点。

### 1. 获取故事树结构
- **URL**: `/api/v1/story/tree`
- **Method**: `GET`
- **功能**: 获取指定活动的故事树（返回根节点列表，递归包含 children）
- **查询参数**:
  - `book_id`: 必填，活动 ID
- **响应 200**: `StoryNodeTreeItem` 数组（每个节点包含 author、状态、点赞数、children 等，但不含正文 content）
- **注意**: 返回的数据不含节点正文（content），仅用于展示树形结构。正文需通过详情接口获取。

### 2. 获取阅读路径 (溯源)
- **URL**: `/api/v1/story/node/{node_id}/path`
- **Method**: `GET`
- **功能**: 返回从根节点到当前节点的路径（按深度升序），用于“故事溯源”或面包屑导航。
- **路径参数**: `node_id`
- **响应 200**: `StoryNodeRead` 数组（包含每个节点的基本信息，含 summary 但不含 content）
- **响应 404**: 节点不存在或无权访问

### 3. 提交续写内容 (创建节点)
- **URL**: `/api/v1/story/node`
- **Method**: `POST`
- **功能**: 用户为某个父节点续写一段内容（需登录）
- **请求体 (JSON)**:
  ```json
  {
    "book_id": 1,
    "parent_id": 123,           // 可选，如果为根节点则留空或null
    "title": "章节标题",          // 可选
    "content": "至少10个字符的内容...",
    "branch_name": "分支名"       // 可选
  }
  ```
- **响应 200**: 创建的节点简要信息 `StoryNodeListItem`
- **错误**:
  - 400: 活动已关闭或该分支已完结
  - 401: 未登录
  - 403: 无权限（如用户被禁言）
  - 404: 父节点不存在

### 4. 查看节点正文详情
- **URL**: `/api/v1/story/node/{node_id}`
- **Method**: `GET`
- **功能**: 获取节点的完整正文内容（content）
- **路径参数**: `node_id`
- **响应 200**: `StoryNodeRead`（包含 content）
- **响应 403**: 节点处于 pending 且非作者/管理员，不可见
- **响应 404**: 节点不存在

### 5. 修改节点内容
- **URL**: `/api/v1/story/node/{node_id}`
- **Method**: `PATCH`
- **功能**: 修改自己的节点内容（仅限 pending 或 rejected 状态？需确认，文档未明确状态限制）
- **路径参数**: `node_id`
- **查询参数** (均在 query 中):
  - `title`: 新标题
  - `content`: 新正文（至少10字符）
  - `branch_name`: 新分支名
- **响应 200**: 更新后的 `StoryNodeRead`

### 6. 删除叶子节点
- **URL**: `/api/v1/story/node/{node_id}`
- **Method**: `DELETE`
- **功能**: 删除节点（必须是叶子节点，即没有子节点）
- **路径参数**: `node_id`
- **响应 200**: `{ "detail": "删除成功" }`
- **注意**: 可能只有作者或管理员可删除，文档未标注权限。

### 7. 获取用户的创作列表
- **URL**: `/api/v1/story/user/{user_id}/nodes`
- **Method**: `GET`
- **功能**: 查看某个用户创作的节点列表（支持按状态过滤）
- **路径参数**: `user_id`
- **查询参数**:
  - `status`: 可选，过滤节点状态（pending/published/locked/rejected）
  - `skip`: 默认 0
  - `limit`: 默认 50，最大 200
- **响应 200**: `StoryNodeListItem` 数组

---

## 互动模块 (`/interaction`)

### 1. 点赞/取消点赞 (Toggle)
- **URL**: `/api/v1/interaction/node/{node_id}/like`
- **Method**: `POST`
- **功能**: 对节点进行点赞，如果已点赞则取消（需登录）
- **路径参数**: `node_id`
- **响应 200**:
  ```json
  {
    "status": "success",
    "action": "liked",    // 或 "unliked"
    "likes_count": 123
  }
  ```
- **响应 401/404**

### 2. 获取评论列表
- **URL**: `/api/v1/interaction/node/{node_id}/comments`
- **Method**: `GET`
- **功能**: 分页获取某节点的评论（支持 skip/limit）
- **路径参数**: `node_id`
- **查询参数**: `skip`(0), `limit`(50)
- **响应 200**: `CommentResponse` 数组，包含评论者信息

### 3. 发表评论
- **URL**: `/api/v1/interaction/node/{node_id}/comment`
- **Method**: `POST`
- **功能**: 对节点发表评论（需登录）
- **路径参数**: `node_id`
- **请求体 (JSON)**:
  ```json
  { "content": "评论内容" }
  ```
- **响应 200**: 创建的 `CommentResponse`

### 4. 我的通知列表
- **URL**: `/api/v1/interaction/notifications`
- **Method**: `GET`
- **功能**: 获取当前登录用户的通知（如被点赞、被评论等）
- **查询参数**: `skip`, `limit`
- **响应 200**: `NotificationResponse` 数组

### 5. 一键已读
- **URL**: `/api/v1/interaction/notifications/read`
- **Method**: `PUT`
- **功能**: 将所有未读通知标记为已读
- **响应 200**: `{ "detail": "全部设为已读" }`

---

## 发现模块 (`/discovery`)

### 1. 最新动态 (瀑布流)
- **URL**: `/api/v1/discovery/feed`
- **Method**: `GET`
- **功能**: 获取全站最新发布的节点（published 状态），可按活动过滤
- **查询参数**:
  - `book_id`: 可选，指定活动ID
  - `skip`, `limit`: 默认 0/20，limit 最大 100
- **响应 200**: `StoryNodeListItem` 数组（不含 content）

### 2. 热门分支榜
- **URL**: `/api/v1/discovery/trending`
- **Method**: `GET`
- **功能**: 获取最近 N 天内按点赞数倒序的热门节点
- **查询参数**:
  - `days`: 最近几天，默认 7，范围 1-30
  - `limit`: 返回数量，默认 10，最大 50
- **响应 200**: `StoryNodeListItem` 数组

### 3. 关键词搜索
- **URL**: `/api/v1/discovery/search`
- **Method**: `GET`
- **功能**: 对节点标题和内容进行模糊搜索（LIKE 查询）
- **查询参数**:
  - `q`: 关键词，长度 1-50
  - `limit`: 返回数量，默认 20，最大 100
- **响应 200**: `StoryNodeListItem` 数组

---

## 上传模块 (`/uploads`)

### 上传图片 (返回URL)
- **URL**: `/api/v1/uploads/`
- **Method**: `POST`
- **功能**: 上传图片文件，返回可访问的 URL（可用于头像、封面等）
- **请求体**: `multipart/form-data`，字段名 `file`，文件内容
- **响应 200**:
  ```json
  { "url": "https://storage.example.com/path/to/image.jpg" }
  ```
- **错误**:
  - 400: 文件类型/大小不合法
  - 401: 未登录
- **注意**: 需登录，文件大小和格式限制由后端定义。

---

## 管理员模块 (`/admin`)

### 1. 获取待审核节点列表
- **URL**: `/api/v1/admin/nodes/pending`
- **Method**: `GET`
- **功能**: 管理员专用的审核工作台，列出所有 pending 状态的节点
- **查询参数**: `skip`, `limit`（默认 50）
- **响应 200**: `StoryNodeTreeItem` 数组（不含 content）
- **响应 403**: 非管理员

### 2. 审核/强制修改节点状态
- **URL**: `/api/v1/admin/nodes/{node_id}/audit`
- **Method**: `PATCH`
- **功能**: 管理员审核节点，将状态改为 published/locked/rejected 等
- **路径参数**: `node_id`
- **请求体 (JSON)**:
  ```json
  { "status": "published" }
  ```
- **响应 200**: 更新后的节点信息 `StoryNodeTreeItem`

### 3. 管理员强制修改用户信息
- **URL**: `/api/v1/admin/users/{user_id}`
- **Method**: `PATCH`
- **功能**: 管理员修改用户资料（包括角色、封禁等）
- **路径参数**: `user_id`
- **请求体 (JSON)**:
  ```json
  {
    "role": "banned",          // 可选 admin/writer/banned
    "is_active": false,        // 可选
    "username": "newname",
    "bio": "...",
    "avatar": "..."
  }
  ```
- **响应 200**: 更新后的 `UserResponse`

---

## 附录：数据模型详细说明

### StoryNodeListItem (列表项)
用于 feed、搜索、用户创作列表等，不含 content 和 children。
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 节点ID |
| parent_id | integer/null | 父节点ID |
| book_id | integer | 所属活动ID |
| author | AuthorInfo | 作者信息 |
| title | string/null | 标题 |
| summary | string/null | 摘要（可能由 content 截取） |
| branch_name | string/null | 分支名 |
| status | NodeStatus | 节点状态 |
| depth | integer | 深度（根为0） |
| likes_count | integer | 点赞数 |
| created_at | datetime | 创建时间 |

### StoryNodeRead (详情页)
继承自 StoryNodeListItem，额外增加 `content` 字段。

### StoryNodeTreeItem (树结构)
继承自 StoryNodeListItem，额外增加 `children`（递归包含相同结构）。

### CommentResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 评论ID |
| content | string | 评论内容 |
| created_at | datetime | 评论时间 |
| user | AuthorInfo | 评论者 |

### NotificationResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 通知ID |
| type | string | 通知类型（如 like, comment） |
| sender | AuthorInfo | 触发者 |
| target_id | integer | 相关对象ID（如节点ID） |
| is_read | boolean | 是否已读 |
| created_at | datetime | 时间 |

---

## 错误响应示例

### 422 参数校验错误
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 通用错误 (4xx/5xx)
```json
{ "detail": "错误描述" }
```

---

**以上接口信息基于当前 OpenAPI 文档整理，如有变动请以后端实际实现为准。**