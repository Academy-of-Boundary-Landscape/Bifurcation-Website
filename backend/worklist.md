# 后端功能一览

---

这个文档详细介绍后端所有 API 接口，包括请求格式、响应格式、参数说明等。

如果你想查看在线 API 文档，可以：
1. 启动后端：`python main.py`
2. 访问 Swagger UI: `http://localhost:8057/docs`
3. 访问 ReDoc: `http://localhost:8057/redoc`

---

## 0) 通用约定

### 鉴权方式
- **Bearer Token (JWT)**: 需要登录的接口需要在 Header 中携带 Token
  ```
  Authorization: Bearer <your_access_token>
  ```

### 权限说明
- **游客**: 未登录用户，只能访问公开内容
- **登录用户**: 普通用户，可以创建内容、点赞、评论
- **管理员**: 拥有所有权限，可以审核内容、管理用户

### 分页参数
- `skip`: 跳过的记录数（默认 0）
- `limit`: 返回的记录数（默认 20-100）

### 错误响应格式

#### 通用错误响应
```json
{
  "detail": "错误描述信息"
}
```

#### 验证错误响应
```json
{
  "detail": [
    {
      "loc": ["body", "字段名"],
      "msg": "错误信息",
      "type": "value_error"
    }
  ]
}
```

---

## 1) Auth 模块（认证模块）

### 1.1 发送注册邮箱验证码

**接口**: `POST /api/v1/auth/send-code-for-activation`

**说明**: 向邮箱发送验证码，用于注册前的邮箱验证

**请求格式**:
```json
{
  "email": "user@example.com"
}
```

**参数说明**:
- `email` (string, required): 用户邮箱地址

**响应格式**:

成功 (200):
```json
{
  "detail": "验证码已发送 (测试环境请查看控制台输出或直接使用 114514)"
}
```

失败 (400):
```json
{
  "detail": "该邮箱已注册并激活，请直接登录"
}
```

**安全限制**:
- 1 分钟内只能发送 1 次验证码

---

### 1.2 验证邮箱验证码

**接口**: `POST /api/v1/auth/verify-email-for-activation`

**说明**: 验证邮箱验证码，用于激活账号

**请求格式**:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**参数说明**:
- `email` (string, required): 用户邮箱地址
- `code` (string, required): 6 位验证码

**响应格式**:

成功 (200):
```json
{
  "detail": "邮箱验证成功，账号已激活"
}
```

失败 (400):
```json
{
  "detail": "验证码无效或已过期 / 验证码错误"
}
```

**安全限制**:
- 15 分钟内最多尝试 5 次验证码，超过则需等待
- 验证失败会记录尝试次数
- 账号被封禁时无法激活

---

### 1.3 用户注册

**接口**: `POST /api/v1/auth/register`

**说明**: 用户注册，需要邮箱验证码（验证码需先通过 `/send-code-for-activation` 获取）

**请求格式**:
```json
{
  "email": "user@example.com",
  "username": "newuser",
  "password": "password123"
}
```

**参数说明**:
- `email` (string, 2-100 chars, required): 用户邮箱
- `username` (string, 2-50 chars, required): 用户名
- `password` (string, min 6 chars, required): 密码（至少 6 位）

**前置条件**:
- 用户需先调用 `/send-code-for-activation` 获取邮箱验证码
- 注册时会验证邮箱验证码的有效性，验证码使用后失效

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "newuser",
  "role": "writer",
  "is_active": true,
  "is_verified": false,
  "bio": null,
  "avatar": "https://example.com/avatar.jpg",
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T12:00:00Z"
}
```

---

### 1.4 用户登录

**接口**: `POST /api/v1/auth/login`

**说明**: 登录获取 Token，支持邮箱或用户名登录

**请求格式** (application/x-www-form-urlencoded):
```
username: user@example.com 或 newuser
password: password123
grant_type: password
```

**参数说明**:
- `username` (string, required): 邮箱或用户名
- `password` (string, required): 密码
- `grant_type` (string, optional): 固定为 "password"

**响应格式**:

成功 (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 1.5 获取当前用户信息

**接口**: `GET /api/v1/auth/me`

**说明**: 获取当前登录用户的详细信息

**权限**: 需要登录

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "newuser",
  "role": "writer",
  "is_active": true,
  "is_verified": true,
  "bio": "这是我的简介",
  "avatar": "https://example.com/avatar.jpg",
  "nodes_count": 10,
  "likes_count": 50,
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T12:00:00Z"
}
```

**字段说明**:
- `role`: "admin" | "writer" | "banned"
- `is_active`: 用户是否激活（未封禁）
- `is_verified`: 邮箱是否已验证
- `nodes_count`: 用户创作的节点数
- `likes_count`: 用户获得的点赞数

---

### 1.6 修改个人资料

**接口**: `PATCH /api/v1/auth/me`

**说明**: 修改当前用户的个人信息

**权限**: 需要登录

**请求格式**:
```json
{
  "username": "newusername",
  "bio": "更新后的简介",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**参数说明**:
- `username` (string, 2-50 chars, optional): 新用户名
- `bio` (string, max 200 chars, optional): 个人简介
- `avatar` (string, optional): 头像链接

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "newusername",
  "role": "writer",
  "is_active": true,
  "is_verified": true,
  "bio": "更新后的简介",
  "avatar": "https://example.com/new-avatar.jpg",
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T12:00:00Z"
}
```

---

### 1.7 发送重置密码验证码

**接口**: `POST /api/v1/auth/send-code-for-password-reset`

**说明**: 发送重置密码的验证码到已注册邮箱

**请求格式**:
```json
{
  "email": "user@example.com"
}
```

**参数说明**:
- `email` (string, required): 用户邮箱地址

**响应格式**:

成功 (200):
```json
{
  "detail": "验证码已发送 (测试环境请查看控制台输出或直接使用 114514)"
}
```

失败 (400):
```json
{
  "detail": "该邮箱未注册 / 该账号已被封禁"
}
```

**安全限制**:
- 1 分钟内最多发送 2 次验证码

---

### 1.8 重置密码

**接口**: `POST /api/v1/auth/reset-password`

**说明**: 使用验证码重置密码

**请求格式**:
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "newpassword123"
}
```

**参数说明**:
- `email` (string, required): 用户邮箱地址
- `code` (string, required): 6 位验证码
- `new_password` (string, min 6 chars, required): 新密码

**响应格式**:

成功 (200):
```json
{
  "detail": "密码重置成功"
}
```

**流程说明**:
1. 用户先调用 `/send-code-for-password-reset` 获取验证码
2. 用户收到邮件后，调用此接口提交新密码和验证码

---

### 1.9 登录态修改密码

**接口**: `POST /api/v1/auth/change-password`

**说明**: 登录用户修改密码（需要当前密码）

**权限**: 需要登录

**请求格式**:
```json
{
  "old_password": "currentpassword",
  "new_password": "newpassword123"
}
```

**响应格式**:

成功 (200):
```json
{
  "detail": "密码修改成功"
}
```

---

## 2) Users 模块（用户模块）

### 2.1 查看用户主页

**接口**: `GET /api/v1/users/{user_id}`

**说明**: 查看指定用户的公开信息（游客可用）

**路径参数**:
- `user_id` (integer, required): 要查看的用户 ID

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "newuser",
  "role": "writer",
  "is_active": true,
  "is_verified": true,
  "bio": "这是我的简介",
  "avatar": "https://example.com/avatar.jpg",
  "nodes_count": 10,
  "likes_count": 50,
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T12:00:00Z"
}
```

---

## 3) StoryBook 模块（故事书/活动模块）

### 3.1 获取活动列表

**接口**: `GET /api/v1/story/books`

**说明**: 获取所有活动的列表（游客可用）

**查询参数**:
- `phase` (string, optional): 活动阶段筛选 ("writing" | "showcase" | "archived")
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 100, max: 200): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "title": "奇幻冒险",
    "description": "一个关于魔法与冒险的故事",
    "cover_image": "https://example.com/cover.jpg",
    "phase": "writing",
    "allow_new_nodes": true,
    "is_active": true,
    "start_at": "2026-02-01T00:00:00Z",
    "writing_end_at": "2026-03-01T00:00:00Z",
    "showcase_end_at": "2026-04-01T00:00:00Z",
    "created_at": "2026-02-06T12:00:00Z"
  }
]
```

---

### 3.2 创建活动

**接口**: `POST /api/v1/story/books`

**说明**: 创建新的故事书活动

**权限**: 需要管理员权限

**请求格式**:
```json
{
  "title": "新的故事活动",
  "description": "这是一个全新的故事活动",
  "cover_image": "https://example.com/cover.jpg",
  "phase": "writing",
  "allow_new_nodes": true
}
```

**响应格式**:

成功 (200):
```json
{
  "id": 2,
  "title": "新的故事活动",
  "description": "这是一个全新的故事活动",
  "cover_image": "https://example.com/cover.jpg",
  "phase": "writing",
  "allow_new_nodes": true,
  "is_active": true,
  "created_at": "2026-02-06T13:00:00Z"
}
```

---

### 3.3 更新活动

**接口**: `PATCH /api/v1/story/books/{book_id}`

**说明**: 更新活动信息

**权限**: 需要管理员权限

**路径参数**:
- `book_id` (integer, required): 活动 ID

**请求格式** (Query Params):
```json
{
  "title": "更新后的标题",
  "description": "更新后的描述",
  "cover_image": "https://example.com/new-cover.jpg",
  "phase": "showcase",
  "allow_new_nodes": false
}
```

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "title": "更新后的标题",
  "description": "更新后的描述",
  "cover_image": "https://example.com/new-cover.jpg",
  "phase": "showcase",
  "allow_new_nodes": false,
  "is_active": true,
  "created_at": "2026-02-06T12:00:00Z"
}
```

---

## 4) StoryNode 模块（故事节点模块）

### 节点状态说明

| 状态 | 说明 | 可见性 |
|------|------|--------|
| `pending` | 待审核 | 仅作者和管理员可见 |
| `published` | 已发布 | 所有人可见 |
| `archived` | 已归档/驳回/删除 | 仅作者和管理员可见 |

### 分支完结标志
- `is_ending: true` 表示该分支已完结，无法继续续写

---

### 4.1 获取故事树结构

**接口**: `GET /api/v1/story/tree`

**说明**: 获取整棵故事树的结构（带权限控制）

**查询参数**:
- `book_id` (integer, required): 活动 ID

**权限规则**:
- 管理员：看到全部节点
- 登录用户：看到 published + 自己写的
- 游客：只看 published

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 1,
      "username": "author",
      "avatar": "https://example.com/avatar.jpg"
    },
    "title": "故事开始",
    "summary": "这是故事的摘要",
    "branch_name": null,
    "status": "published",
    "visibility": "public",
    "zone": "short",
    "word_count": 100,
    "likes_count": 10,
    "comments_count": 5,
    "children_count": 2,
    "is_ending": false,
    "is_featured": false,
    "published_at": "2026-02-06T12:00:00Z",
    "created_at": "2026-02-06T12:00:00Z",
    "updated_at": "2026-02-06T12:00:00Z",
    "children": [
      {
        "id": 2,
        "parent_id": 1,
        "root_id": 1,
        "book_id": 1,
        "author": {
          "id": 2,
          "username": "user2",
          "avatar": null
        },
        "title": "第一个分支",
        "summary": "分支摘要",
        "branch_name": "选择 A",
        "status": "published",
        "visibility": "public",
        "zone": "short",
        "word_count": 80,
        "likes_count": 5,
        "comments_count": 2,
        "children_count": 0,
        "is_ending": false,
        "is_featured": false,
        "published_at": "2026-02-06T13:00:00Z",
        "created_at": "2026-02-06T13:00:00Z",
        "updated_at": "2026-02-06T13:00:00Z",
        "children": []
      }
    ]
  }
]
```

---

### 4.2 获取节点详情

**接口**: `GET /api/v1/story/node/{node_id}`

**说明**: 获取节点的完整内容（包括正文）

**路径参数**:
- `node_id` (integer, required): 节点 ID

**权限规则**:
- 作者/管理员：可看 pending/archived
- 其他用户：只能看 published

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "parent_id": null,
  "root_id": 1,
  "book_id": 1,
  "author": {
    "id": 1,
    "username": "author",
    "avatar": "https://example.com/avatar.jpg"
  },
  "title": "故事开始",
  "summary": "这是故事的摘要",
  "branch_name": null,
  "status": "published",
  "visibility": "public",
  "zone": "short",
  "word_count": 100,
  "likes_count": 10,
  "comments_count": 5,
  "children_count": 2,
  "is_ending": false,
  "is_featured": false,
  "published_at": "2026-02-06T12:00:00Z",
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T12:00:00Z",
  "content": "这是故事的具体内容，包含完整的正文..."
}
```

失败 (403):
```json
{
  "detail": "该内容正在审核中或已归档，无权访问"
}
```

---

### 4.3 获取阅读路径

**接口**: `GET /api/v1/story/node/{node_id}/path`

**说明**: 获取从根节点到当前节点的路径（溯源）

**路径参数**:
- `node_id` (integer, required): 节点 ID

**权限规则**: 与获取节点详情相同

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 1,
      "username": "author",
      "avatar": null
    },
    "title": "故事开始",
    "summary": "根节点摘要",
    "branch_name": null,
    "status": "published",
    "content": "根节点内容",
    ...
  },
  {
    "id": 2,
    "parent_id": 1,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 2,
      "username": "user2",
      "avatar": null
    },
    "title": "第一个分支",
    "summary": "分支摘要",
    "branch_name": "选择 A",
    "status": "published",
    "content": "分支内容",
    ...
  }
]
```

---

### 4.4 提交续写

**接口**: `POST /api/v1/story/node`

**说明**: 提交新的故事节点续写

**权限**: 需要登录

**请求格式**:
```json
{
  "book_id": 1,
  "parent_id": 2,
  "title": "新的章节",
  "content": "这是新的故事内容，至少 10 个字符...",
  "branch_name": "选择 B",
  "summary": "章节摘要",
  "zone": "short"
}
```

**参数说明**:
- `book_id` (integer, required): 活动 ID
- `parent_id` (integer, optional): 父节点 ID（根节点可以为 null）
- `title` (string, max 120 chars, optional): 节点标题
- `content` (string, min 10 chars, required): 节点内容
- `branch_name` (string, max 80 chars, optional): 分支名称
- `summary` (string, max 600 chars, optional): 节点摘要
- `zone` (string, optional): 节点类型 ("long" | "short")

**响应格式**:

成功 (200):
```json
{
  "id": 3,
  "parent_id": 2,
  "root_id": 1,
  "book_id": 1,
  "author": {
    "id": 1,
    "username": "author",
    "avatar": null
  },
  "title": "新的章节",
  "summary": null,
  "branch_name": "选择 B",
  "status": "pending",
  "visibility": "private",
  "zone": "short",
  "word_count": 50,
  "likes_count": 0,
  "comments_count": 0,
  "children_count": 0,
  "is_ending": false,
  "is_featured": false,
  "published_at": null,
  "created_at": "2026-02-06T14:00:00Z",
  "updated_at": "2026-02-06T14:00:00Z"
}
```

**权限规则**:
- 管理员创建：直接发布（status=published）
- 普通用户创建：进入待审核（status=pending）

失败 (400):
```json
{
  "detail": "当前活动阶段不允许投稿 / 活动已暂停接受新投稿 / 该分支已完结"
}
```

失败 (403):
```json
{
  "detail": "只有管理员可以创建开篇 / 无法在未发布节点后续写"
}
```

---

### 4.5 修改节点内容

**接口**: `PATCH /api/v1/story/node/{node_id}`

**说明**: 修改已存在的节点内容

**权限**: 需要登录，仅作者或管理员可修改

**路径参数**:
- `node_id` (integer, required): 节点 ID

**请求格式** (Query Params):
```json
{
  "title": "修改后的标题",
  "content": "修改后的内容",
  "branch_name": "修改后的分支名",
  "summary": "修改后的摘要"
}
```

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "parent_id": null,
  "root_id": 1,
  "book_id": 1,
  "author": {
    "id": 1,
    "username": "author",
    "avatar": null
  },
  "title": "修改后的标题",
  "summary": null,
  "branch_name": null,
  "status": "published",
  "visibility": "public",
  "zone": "short",
  "word_count": 120,
  "likes_count": 10,
  "comments_count": 5,
  "children_count": 2,
  "is_ending": false,
  "is_featured": false,
  "published_at": "2026-02-06T12:00:00Z",
  "created_at": "2026-02-06T12:00:00Z",
  "updated_at": "2026-02-06T15:00:00Z",
  "content": "修改后的内容"
}
```

---

### 4.6 软删除节点

**接口**: `DELETE /api/v1/story/node/{node_id}`

**说明**: 软删除节点（标记为 archived，而非真正删除）

**权限**: 需要登录，仅作者或管理员可删除

**路径参数**:
- `node_id` (integer, required): 节点 ID

**响应格式**:

成功 (200):
```json
{
  "detail": "节点已归档"
}
```

**说明**:
- 删除后节点状态变为 `archived`
- 仅作者和管理员可查看被删除的节点
- 不会检查节点是否有子节点（允许删除有子节点的节点）
- 删除后会自动更新父节点的 `children_count` 计数器

---

### 4.7 获取用户创作列表

**接口**: `GET /api/v1/story/user/{user_id}/nodes`

**说明**: 获取指定用户创作的节点列表

**路径参数**:
- `user_id` (integer, required): 用户 ID

**查询参数**:
- `status` (string, optional): 节点状态筛选 ("pending" | "published" | "archived")
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 50, max: 200): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 1,
      "username": "author",
      "avatar": null
    },
    "title": "我的创作",
    "summary": "摘要",
    "branch_name": null,
    "status": "published",
    "visibility": "public",
    "zone": "short",
    "word_count": 100,
    "likes_count": 10,
    "comments_count": 5,
    "children_count": 2,
    "is_ending": false,
    "is_featured": false,
    "published_at": "2026-02-06T12:00:00Z",
    "created_at": "2026-02-06T12:00:00Z",
    "updated_at": "2026-02-06T12:00:00Z"
  }
]
```

---

## 5) Interaction 模块（互动模块）

### 5.1 点赞/取消点赞

**接口**: `POST /api/v1/interaction/node/{node_id}/like`

**说明**: 对节点进行点赞或取消点赞（Toggle 操作）

**权限**: 需要登录

**路径参数**:
- `node_id` (integer, required): 节点 ID

**响应格式**:

成功 (200):
```json
{
  "status": "success",
  "action": "liked",
  "likes_count": 11
}
```

或

```json
{
  "status": "success",
  "action": "unliked",
  "likes_count": 10
}
```

---

### 5.2 获取评论列表

**接口**: `GET /api/v1/interaction/node/{node_id}/comments`

**说明**: 获取节点的评论列表（游客可用）

**路径参数**:
- `node_id` (integer, required): 节点 ID

**查询参数**:
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 50, max: 100): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "content": "这个故事很有趣！",
    "created_at": "2026-02-06T14:00:00Z",
    "user": {
      "id": 2,
      "username": "commenter",
      "avatar": "https://example.com/avatar.jpg"
    }
  },
  {
    "id": 2,
    "content": "期待后续发展",
    "created_at": "2026-02-06T15:00:00Z",
    "user": {
      "id": 3,
      "username": "reader",
      "avatar": null
    }
  }
]
```

---

### 5.3 发表评论

**接口**: `POST /api/v1/interaction/node/{node_id}/comment`

**说明**: 对节点发表评论

**权限**: 需要登录

**路径参数**:
- `node_id` (integer, required): 节点 ID

**请求格式**:
```json
{
  "content": "这是我的评论内容"
}
```

**参数说明**:
- `content` (string, required): 评论内容

**响应格式**:

成功 (200):
```json
{
  "id": 3,
  "content": "这是我的评论内容",
  "created_at": "2026-02-06T16:00:00Z",
  "user": {
    "id": 1,
    "username": "myself",
    "avatar": "https://example.com/avatar.jpg"
  }
}
```

---

### 5.4 获取通知列表

**接口**: `GET /api/v1/interaction/notifications`

**说明**: 获取当前用户的通知列表

**权限**: 需要登录

**查询参数**:
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 50, max: 100): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "type": "branched",
    "sender": {
      "id": 2,
      "username": "user2",
      "avatar": null
    },
    "target_id": 5,
    "is_read": false,
    "created_at": "2026-02-06T14:00:00Z"
  },
  {
    "id": 2,
    "type": "liked",
    "sender": {
      "id": 3,
      "username": "user3",
      "avatar": "https://example.com/avatar.jpg"
    },
    "target_id": 1,
    "is_read": true,
    "created_at": "2026-02-06T13:00:00Z"
  }
]
```

**字段说明**:
- `type`: "branched" | "liked" | "commented" | "approved" | "rejected"
- `target_id`: 关联的节点 ID 或评论 ID

---

### 5.5 获取未读通知数

**接口**: `GET /api/v1/interaction/notifications/unread-count`

**说明**: 获取当前用户的未读通知数量

**权限**: 需要登录

**响应格式**:

成功 (200):
```json
{
  "unread_count": 5
}
```

---

### 5.6 单条通知标记已读

**接口**: `PUT /api/v1/interaction/notifications/{notification_id}/read`

**说明**: 将单条通知标记为已读

**权限**: 需要登录

**路径参数**:
- `notification_id` (integer, required): 通知 ID

**响应格式**:

成功 (200):
```json
{
  "detail": "通知已标记为已读"
}
```

---

### 5.7 一键已读通知

**接口**: `PUT /api/v1/interaction/notifications/read`

**说明**: 将所有通知标记为已读

**权限**: 需要登录

**响应格式**:

成功 (200):
```json
{
  "detail": "全部通知已标记为已读"
}
```

---

### 5.8 软删除评论

**接口**: `DELETE /api/v1/interaction/comment/{comment_id}`

**说明**: 软删除评论（标记为 deleted，而非真正删除）

**权限**: 需要登录，仅评论作者或管理员可删除

**路径参数**:
- `comment_id` (integer, required): 评论 ID

**响应格式**:

成功 (200):
```json
{
  "detail": "评论已删除"
}
```

**说明**:
- 删除后评论从列表消失（通过 `deleted_at` 字段过滤）
- 删除后会自动更新节点的 `comments_count` 计数器
- 评论作者和管理员可随时删除自己的评论

---

## 6) Discovery 模块（发现模块）

### 6.1 最新动态

**接口**: `GET /api/v1/discovery/feed`

**说明**: 获取全站最新发布的节点（游客可用）

**查询参数**:
- `book_id` (integer, optional): 只看某个活动的动态
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 20, max: 100): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 10,
    "parent_id": 5,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 3,
      "username": "author3",
      "avatar": null
    },
    "title": "最新章节",
    "summary": "这是最新发布的章节",
    "branch_name": "新分支",
    "status": "published",
    "visibility": "public",
    "zone": "short",
    "word_count": 150,
    "likes_count": 2,
    "comments_count": 1,
    "children_count": 0,
    "is_ending": false,
    "is_featured": false,
    "published_at": "2026-02-06T16:00:00Z",
    "created_at": "2026-02-06T16:00:00Z",
    "updated_at": "2026-02-06T16:00:00Z"
  }
]
```

---

### 6.2 热门榜单

**接口**: `GET /api/v1/discovery/trending`

**说明**: 获取最近 N 天内最热门的节点（按点赞数排序）

**查询参数**:
- `days` (integer, optional, default: 7, min: 1, max: 30): 统计最近几天的热度
- `limit` (integer, optional, default: 10, min: 1, max: 50): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 1,
      "username": "author1",
      "avatar": "https://example.com/avatar.jpg"
    },
    "title": "热门故事",
    "summary": "这是最热门的故事",
    "branch_name": null,
    "status": "published",
    "visibility": "public",
    "zone": "short",
    "word_count": 200,
    "likes_count": 100,
    "comments_count": 20,
    "children_count": 5,
    "is_ending": false,
    "is_featured": false,
    "published_at": "2026-02-01T12:00:00Z",
    "created_at": "2026-02-01T12:00:00Z",
    "updated_at": "2026-02-06T12:00:00Z"
  }
]
```

---

### 6.3 关键词搜索

**接口**: `GET /api/v1/discovery/search`

**说明**: 搜索节点（支持标题、内容的模糊搜索）

**查询参数**:
- `q` (string, 1-50 chars, required): 搜索关键词
- `limit` (integer, optional, default: 20, min: 1, max: 100): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 5,
    "parent_id": 2,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 3,
      "username": "author3",
      "avatar": null
    },
    "title": "魔法世界",
    "summary": "这是一个关于魔法的故事",
    "branch_name": "魔法分支",
    "status": "published",
    "visibility": "public",
    "zone": "short",
    "word_count": 180,
    "likes_count": 15,
    "comments_count": 3,
    "children_count": 1,
    "is_ending": false,
    "is_featured": false,
    "published_at": "2026-02-03T14:00:00Z",
    "created_at": "2026-02-03T14:00:00Z",
    "updated_at": "2026-02-03T14:00:00Z"
  }
]
```

---

## 7) Admin 模块（管理员模块）

### 7.1 获取待审核节点

**接口**: `GET /api/v1/admin/nodes/pending`

**说明**: 获取所有待审核的节点列表

**权限**: 需要管理员权限

**查询参数**:
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 50, max: 200): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 10,
    "parent_id": 5,
    "root_id": 1,
    "book_id": 1,
    "author": {
      "id": 4,
      "username": "author4",
      "avatar": null
    },
    "title": "待审核章节",
    "summary": "等待审核的内容",
    "branch_name": "新分支",
    "status": "pending",
    "visibility": "private",
    "zone": "short",
    "word_count": 100,
    "likes_count": 0,
    "comments_count": 0,
    "children_count": 0,
    "is_ending": false,
    "is_featured": false,
    "published_at": null,
    "created_at": "2026-02-06T17:00:00Z",
    "updated_at": "2026-02-06T17:00:00Z",
    "children": []
  }
]
```

---

### 7.2 审核节点

**接口**: `PATCH /api/v1/admin/nodes/{node_id}/audit`

**说明**: 审核节点（通过、驳回/归档）

**权限**: 需要管理员权限

**路径参数**:
- `node_id` (integer, required): 节点 ID

**请求格式**:
```json
{
  "status": "published",
  "reject_reason": null
}
```

**参数说明**:
- `status` (string, required): 新的节点状态
  - "published": 通过审核，发布
  - "archived": 驳回/归档
- `reject_reason` (string, optional): 驳回/归档原因

**响应格式**:

成功 (200):
```json
{
  "id": 10,
  "parent_id": 5,
  "root_id": 1,
  "book_id": 1,
  "author": {
    "id": 4,
    "username": "author4",
    "avatar": null
  },
  "title": "待审核章节",
  "summary": "等待审核的内容",
  "branch_name": "新分支",
  "status": "published",
  "visibility": "public",
  "zone": "short",
  "word_count": 100,
  "likes_count": 0,
  "comments_count": 0,
  "children_count": 0,
  "is_ending": false,
  "is_featured": false,
  "published_at": "2026-02-06T18:00:00Z",
  "created_at": "2026-02-06T17:00:00Z",
  "updated_at": "2026-02-06T18:00:00Z",
  "children": []
}
```

---

### 7.3 管理用户

**接口**: `PATCH /api/v1/admin/users/{user_id}`

**说明**: 管理员强制修改用户信息（封禁、改角色等）

**权限**: 需要管理员权限

**路径参数**:
- `user_id` (integer, required): 用户 ID

**请求格式**:
```json
{
  "role": "banned",
  "is_active": false,
  "username": "修改后的用户名",
  "bio": "修改后的简介",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**参数说明**:
- `role` (string, optional): 用户角色 ("admin" | "writer" | "banned")
- `is_active` (boolean, optional): 是否激活（false 表示封禁）
- `username` (string, optional): 新用户名
- `bio` (string, optional): 新简介
- `avatar` (string, optional): 新头像链接

**响应格式**:

成功 (200):
```json
{
  "id": 2,
  "email": "user2@example.com"
  "username": "修改后的用户名",
  "role": "banned",
  "is_active": false,
  "is_verified": true,
  "bio": "修改后的简介",
  "avatar": "https://example.com/new-avatar.jpg",
  "created_at": "2026-02-01T12:00:00Z",
  "updated_at": "2026-02-06T18:00:00Z"
}
```

---

### 7.4 获取用户列表

**接口**: `GET /api/v1/admin/users`

**说明**: 获取用户列表（支持筛选）

**权限**: 需要管理员权限

**查询参数**:
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 50, max: 200): 返回的记录数
- `role` (string, optional): 按角色筛选 ("admin" | "writer" | "banned")
- `is_active` (boolean, optional): 按活跃状态筛选
- `keyword` (string, optional): 邮箱/用户名关键词

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "username": "user1",
    "role": "writer",
    "is_active": true,
    "is_verified": true,
    "bio": "简介",
    "avatar": "https://example.com/avatar.jpg",
    "created_at": "2026-02-01T12:00:00Z",
    "updated_at": "2026-02-06T12:00:00Z"
  }
]
```

---

### 7.5 仪表盘统计

**接口**: `GET /api/v1/admin/stats`

**说明**: 获取后台管理仪表盘统计数据

**权限**: 需要管理员权限

**响应格式**:

成功 (200):
```json
{
  "users": {
    "total": 100,
    "active": 90,
    "inactive": 10,
    "new_7d": 15
  },
  "nodes": {
    "total": 500,
    "pending": 20,
    "published": 450,
    "archived": 30,
    "new_7d": 50
  }
}
```

---

## 8) Upload 模块（上传模块）

### 8.1 上传图片

**接口**: `POST /api/v1/uploads/`

**说明**: 上传图片文件，返回图片 URL

**权限**: 需要登录

**请求格式** (multipart/form-data):
```
file: <二进制图片文件>
```

**参数说明**:
- `file` (binary, required): 图片文件

**文件限制**:
- 文件类型：image/jpeg, image/png, image/gif, image/webp
- 文件大小：最大 5MB
- 允许后缀：jpg, jpeg, png, gif, webp

**响应格式**:

成功 (200):
```json
{
  "url": "/static/uploads/abc123.jpg"
}
```

---

## 附录：数据类型定义

### NodeStatus（节点状态）
| 状态 | 说明 | 可见性 |
|------|------|--------|
| `pending` | 待审核 | 仅作者和管理员可见 |
| `published` | 已发布 | 所有人可见 |
| `archived` | 已归档/驳回/删除 | 仅作者和管理员可见 |

### NodeVisibility（节点可见性）
| 可见性 | 说明 |
|--------|------|
| `private` | 私有，待审/作者自见 |
| `public` | 公开，对外发布 |
| `unlisted` | 不列入列表，直链可访问 |

### UserRole（用户角色）
| 角色 | 说明 |
|------|------|
| `admin` | 管理员 |
| `writer` | 普通写手 |
| `banned` | 被封禁 |

### BookPhase（活动阶段）
| 阶段 | 说明 |
|------|------|
| `writing` | 创作阶段，允许投稿 |
| `showcase` | 展示阶段，不允许新投稿 |
| `archived` | 已归档 |

### AuthorInfo（作者信息）
```json
{
  "id": 1,
  "username": "author",
  "avatar": "https://example.com/avatar.jpg"
}
```

---

## 最小可上线版本（MVP）需要的接口

### 认证
- ✅ `POST /api/v1/auth/send-code-for-activation` - 发送注册验证码
- ✅ `POST /api/v1/auth/register` - 用户注册
- ✅ `POST /api/v1/auth/login` - 用户登录
- ✅ `GET /api/v1/auth/me` - 获取当前用户信息

### 故事书
- ✅ `GET /api/v1/story/books` - 获取活动列表

### 故事节点
- ✅ `GET /api/v1/story/tree` - 获取故事树结构
- ✅ `GET /api/v1/story/node/{node_id}` - 获取节点详情
- ✅ `GET /api/v1/story/node/{node_id}/path` - 获取阅读路径
- ✅ `POST /api/v1/story/node` - 提交续写

### 互动
- ✅ `POST /api/v1/interaction/node/{node_id}/like` - 点赞/取消点赞
- ✅ `GET /api/v1/interaction/node/{node_id}/comments` - 获取评论列表
- ✅ `POST /api/v1/interaction/node/{node_id}/comment` - 发表评论
- ✅ `GET /api/v1/interaction/notifications` - 获取通知列表
- ✅ `PUT /api/v1/interaction/notifications/read` - 一键已读

### 发现
- ✅ `GET /api/v1/discovery/feed` - 最新动态
- ✅ `GET /api/v1/discovery/trending` - 热门榜单
- ✅ `GET /api/v1/discovery/search` - 关键词搜索

### 上传
- ✅ `POST /api/v1/uploads/` - 上传图片

### 管理员
- ✅ `GET /api/v1/admin/nodes/pending` - 获取待审核节点
- ✅ `PATCH /api/v1/admin/nodes/{node_id}/audit` - 审核节点
- ✅ `PATCH /api/v1/admin/users/{user_id}` - 管理用户

### 用户
- ✅ `GET /api/v1/users/{user_id}` - 查看用户主页

---

**文档版本**: 2.3  
**更新日期**: 2026-03-07  
**更新日志**:
- v2.3: 添加 CORS 跨域配置，支持前端开发环境
- v2.3: 添加全局异常处理（404/500）
- v2.3: 新增健康检查端点 `GET /health`
- v2.3: 添加 `CORS_ORIGINS` 配置项
- v2.2: 修复注册接口未验证邮箱验证码的问题
- v2.2: 添加 15 分钟 5 次验证码尝试限制
- v2.2: 统一密码强度规则为至少 6 位（与文档一致）
- v2.2: 添加账号封禁检查到邮箱验证接口
- v2.2: 修复节点删除时父节点 children_count 不同步的问题
- v2.2: 新增评论删除接口，同步更新节点 comments_count
- v2.1: 修正节点状态定义为 `pending | published | archived`，`archived` 统一表示驳回/删除
- v2.1: 添加验证码安全限制（1 分钟 2 次，15 分钟 5 次尝试）
- v2.1: 添加评论计数器同步更新说明

**说明**: 本文档基于实际代码实现整理，包含所有接口的详细请求和响应格式