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

### 1.1 发送邮箱验证码

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
  "detail": "验证码已发送到邮箱"
}
```

失败 (400):
```json
{
  "detail": "邮箱已注册并激活"
}
```

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
- `code` (string, required): 6位验证码

**响应格式**:

成功 (200):
```json
{
  "detail": "邮箱验证成功"
}
```

---

### 1.3 用户注册

**接口**: `POST /api/v1/auth/register`

**说明**: 用户注册，需要邮箱验证码

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
- `password` (string, min 6 chars, required): 密码

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "newuser",
  "role": "writer",
  "is_active": true,
  "is_verified": false
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

### 1.5 发送重置密码验证码

**接口**: `POST /api/v1/auth/send-code-for-password-reset`

**说明**: 发送重置密码的验证码

**请求格式**:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**参数说明**:
- `email` (string, required): 用户邮箱地址
- `code` (string, required): 6位验证码

**响应格式**:

成功 (200):
```json
{
  "detail": "验证码已发送"
}
```

---

### 1.6 重置密码

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
- `code` (string, required): 6位验证码
- `new_password` (string, min 6 chars, required): 新密码

**响应格式**:

成功 (200):
```json
{
  "detail": "密码重置成功"
}
```

---

### 1.7 获取当前用户信息

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
  "likes_count": 50
}
```

**字段说明**:
- `role`: "admin" | "writer" | "banned"
- `is_active`: 用户是否激活（未封禁）
- `is_verified`: 邮箱是否已验证
- `nodes_count`: 用户创作的节点数
- `likes_count`: 用户获得的点赞数

---

### 1.8 修改个人资料

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
  "avatar": "https://example.com/new-avatar.jpg"
}
```

失败 (400):
```json
{
  "detail": "用户被封禁"
}
```

失败 (401):
```json
{
  "detail": "未认证"
}
```

---

## 2) Users 模块（用户模块）

### 2.1 查看用户主页

**接口**: `GET /api/v1/users/{user_id}`

**说明**: 查看指定用户的公开信息（游客可用）

**路径参数**:
- `user_id` (integer, required): 要查看的用户ID

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
  "likes_count": 50
}
```

失败 (404):
```json
{
  "detail": "用户不存在"
}
```

---

## 3) StoryBook 模块（故事书/活动模块）

### 3.1 获取活动列表

**接口**: `GET /api/v1/story/books`

**说明**: 获取所有活动的列表（游客可用）

**查询参数**:
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
    "is_active": true,
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
  "cover_image": "https://example.com/cover.jpg"
}
```

**参数说明**:
- `title` (string, 1-100 chars, required): 活动标题
- `description` (string, optional): 活动描述
- `cover_image` (string, max 255 chars, optional): 封面图片链接

**响应格式**:

成功 (200):
```json
{
  "id": 2,
  "title": "新的故事活动",
  "description": "这是一个全新的故事活动",
  "cover_image": "https://example.com/cover.jpg",
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
- `book_id` (integer, required): 活动ID

**查询参数**:
- `title` (string, 1-100 chars, optional): 新标题
- `description` (string, optional): 新描述
- `cover_image` (string, max 255 chars, optional): 新封面
- `is_active` (boolean, optional): 是否激活

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "title": "更新后的标题",
  "description": "更新后的描述",
  "cover_image": "https://example.com/new-cover.jpg",
  "is_active": false,
  "created_at": "2026-02-06T12:00:00Z"
}
```

---

## 4) StoryNode 模块（故事节点模块）

### 4.1 获取故事树结构

**接口**: `GET /api/v1/story/tree`

**说明**: 获取整棵故事树的结构（带权限控制）

**查询参数**:
- `book_id` (integer, required): 活动ID

**权限规则**:
- 管理员：看到全部节点
- 登录用户：看到 published/locked + 自己写的
- 游客：只看 published/locked

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
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
    "depth": 0,
    "likes_count": 10,
    "created_at": "2026-02-06T12:00:00Z",
    "children": [
      {
        "id": 2,
        "parent_id": 1,
        "book_id": 1,
        "author": {
          "id": 2,
          "username": "user2",
          "avatar": null
        },
        "title": "第一个分支",
        "summary": "分支摘要",
        "branch_name": "选择A",
        "status": "published",
        "depth": 1,
        "likes_count": 5,
        "created_at": "2026-02-06T13:00:00Z",
        "children": []
      }
    ]
  }
]
```

**字段说明**:
- `status`: "pending" | "published" | "locked" | "rejected"
- `depth`: 节点深度（根节点为 0）

---

### 4.2 获取节点详情

**接口**: `GET /api/v1/story/node/{node_id}`

**说明**: 获取节点的完整内容（包括正文）

**路径参数**:
- `node_id` (integer, required): 节点ID

**权限规则**:
- 作者/管理员：可看 pending
- 其他用户：只能看 published/locked

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "parent_id": null,
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
  "depth": 0,
  "likes_count": 10,
  "created_at": "2026-02-06T12:00:00Z",
  "content": "这是故事的具体内容，包含完整的正文..."
}
```

失败 (403):
```json
{
  "detail": "审核中不可见"
}
```

失败 (404):
```json
{
  "detail": "节点不存在"
}
```

---

### 4.3 获取阅读路径

**接口**: `GET /api/v1/story/node/{node_id}/path`

**说明**: 获取从根节点到当前节点的路径（溯源）

**路径参数**:
- `node_id` (integer, required): 节点ID

**权限规则**: 与获取节点详情相同

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
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
    "depth": 0,
    "likes_count": 10,
    "created_at": "2026-02-06T12:00:00Z",
    "content": "根节点内容"
  },
  {
    "id": 2,
    "parent_id": 1,
    "book_id": 1,
    "author": {
      "id": 2,
      "username": "user2",
      "avatar": null
    },
    "title": "第一个分支",
    "summary": "分支摘要",
    "branch_name": "选择A",
    "status": "published",
    "depth": 1,
    "likes_count": 5,
    "created_at": "2026-02-06T13:00:00Z",
    "content": "分支内容"
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
  "content": "这是新的故事内容，至少10个字符...",
  "branch_name": "选择B"
}
```

**参数说明**:
- `book_id` (integer, required): 活动ID
- `parent_id` (integer, optional): 父节点ID（根节点可以为 null）
- `title` (string, max 100 chars, optional): 节点标题
- `content` (string, min 10 chars, required): 节点内容
- `branch_name` (string, max 50 chars, optional): 分支名称

**响应格式**:

成功 (200):
```json
{
  "id": 3,
  "parent_id": 2,
  "book_id": 1,
  "author": {
    "id": 1,
    "username": "author",
    "avatar": null
  },
  "title": "新的章节",
  "summary": null,
  "branch_name": "选择B",
  "status": "pending",
  "depth": 2,
  "likes_count": 0,
  "created_at": "2026-02-06T14:00:00Z"
}
```

失败 (400):
```json
{
  "detail": "活动关闭或分支完结"
}
```

失败 (401):
```json
{
  "detail": "未认证"
}
```

失败 (403):
```json
{
  "detail": "无权创建"
}
```

失败 (404):
```json
{
  "detail": "父节点不存在"
}
```

---

### 4.5 修改节点

**接口**: `PATCH /api/v1/story/node/{node_id}`

**说明**: 修改已存在的节点内容

**权限**: 需要登录，仅作者或管理员可修改

**路径参数**:
- `node_id` (integer, required): 节点ID

**查询参数**:
- `title` (string, max 100 chars, optional): 新标题
- `content` (string, min 10 chars, optional): 新内容
- `branch_name` (string, max 50 chars, optional): 新分支名

**响应格式**:

成功 (200):
```json
{
  "id": 1,
  "parent_id": null,
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
  "depth": 0,
  "likes_count": 10,
  "created_at": "2026-02-06T12:00:00Z",
  "content": "修改后的内容"
}
```

---

### 4.6 删除节点

**接口**: `DELETE /api/v1/story/node/{node_id}`

**说明**: 删除叶子节点（不能有子节点）

**权限**: 需要登录，仅作者或管理员可删除

**路径参数**:
- `node_id` (integer, required): 节点ID

**响应格式**:

成功 (200):
```json
{
  "detail": "节点删除成功"
}
```

---

### 4.7 获取用户创作列表

**接口**: `GET /api/v1/story/user/{user_id}/nodes`

**说明**: 获取指定用户创作的节点列表

**路径参数**:
- `user_id` (integer, required): 用户ID

**查询参数**:
- `status` (string, optional): 节点状态筛选 ("pending" | "published" | "locked" | "rejected")
- `skip` (integer, optional, default: 0): 跳过的记录数
- `limit` (integer, optional, default: 50, max: 200): 返回的记录数

**响应格式**:

成功 (200):
```json
[
  {
    "id": 1,
    "parent_id": null,
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
    "depth": 0,
    "likes_count": 10,
    "created_at": "2026-02-06T12:00:00Z"
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
- `node_id` (integer, required): 节点ID

**响应格式**:

成功 (200):
```json
{
  "status": "liked",
  "action": "like",
  "likes_count": 11
}
```

或

```json
{
  "status": "unliked",
  "action": "unlike",
  "likes_count": 10
}
```

失败 (401):
```json
{
  "detail": "未认证"
}
```

失败 (404):
```json
{
  "detail": "节点不存在"
}
```

---

### 5.2 获取评论列表

**接口**: `GET /api/v1/interaction/node/{node_id}/comments`

**说明**: 获取节点的评论列表（游客可用）

**路径参数**:
- `node_id` (integer, required): 节点ID

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
- `node_id` (integer, required): 节点ID

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

失败 (401):
```json
{
  "detail": "未认证"
}
```

失败 (404):
```json
{
  "detail": "节点不存在"
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
- `target_id`: 关联的节点ID或评论ID

失败 (401):
```json
{
  "detail": "未认证"
}
```

---

### 5.5 一键已读通知

**接口**: `PUT /api/v1/interaction/notifications/read`

**说明**: 将所有通知标记为已读

**权限**: 需要登录

**响应格式**:

成功 (200):
```json
{
  "detail": "全部设为已读"
}
```

失败 (401):
```json
{
  "detail": "未认证"
}
```

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
    "depth": 3,
    "likes_count": 2,
    "created_at": "2026-02-06T16:00:00Z"
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
    "depth": 0,
    "likes_count": 100,
    "created_at": "2026-02-01T12:00:00Z"
  },
  {
    "id": 2,
    "parent_id": 1,
    "book_id": 1,
    "author": {
      "id": 2,
      "username": "author2",
      "avatar": null
    },
    "title": "热门分支",
    "summary": "这是热门分支",
    "branch_name": "选择A",
    "status": "published",
    "depth": 1,
    "likes_count": 85,
    "created_at": "2026-02-02T13:00:00Z"
  }
]
```

---

### 6.3 关键词搜索

**接口**: `GET /api/v1/discovery/search`

**说明**: 搜索节点（支持标题、摘要、分支名的模糊搜索）

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
    "depth": 2,
    "likes_count": 15,
    "created_at": "2026-02-03T14:00:00Z"
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
    "depth": 3,
    "likes_count": 0,
    "created_at": "2026-02-06T17:00:00Z",
    "children": []
  }
]
```

失败 (401):
```json
{
  "detail": "未认证"
}
```

失败 (403):
```json
{
  "detail": "权限不足"
}
```

---

### 7.2 审核节点

**接口**: `PATCH /api/v1/admin/nodes/{node_id}/audit`

**说明**: 审核节点（通过、驳回、锁定）

**权限**: 需要管理员权限

**路径参数**:
- `node_id` (integer, required): 节点ID

**请求格式**:
```json
{
  "status": "published"
}
```

**参数说明**:
- `status` (string, required): 新的节点状态
  - "published": 通过审核，发布
  - "rejected": 驳回
  - "locked": 锁定

**响应格式**:

成功 (200):
```json
{
  "id": 10,
  "parent_id": 5,
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
  "depth": 3,
  "likes_count": 0,
  "created_at": "2026-02-06T17:00:00Z",
  "children": []
}
```

失败 (403):
```json
{
  "detail": "权限不足"
}
```

失败 (404):
```json
{
  "detail": "节点不存在"
}
```

---

### 7.3 管理用户

**接口**: `PATCH /api/v1/admin/users/{user_id}`

**说明**: 管理员强制修改用户信息（封禁、改角色等）

**权限**: 需要管理员权限

**路径参数**:
- `user_id` (integer, required): 用户ID

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
  "email": "user2@example.com",
  "username": "修改后的用户名",
  "role": "banned",
  "is_active": false,
  "is_verified": true,
  "bio": "修改后的简介",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

失败 (403):
```json
{
  "detail": "权限不足"
}
```

失败 (404):
```json
{
  "detail": "用户不存在"
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

**响应格式**:

成功 (200):
```json
{
  "url": "http://localhost:8057/static/uploads/2026/02/06/abc123.jpg"
}
```

失败 (400):
```json
{
  "detail": "文件类型/大小不合法"
}
```

失败 (401):
```json
{
  "detail": "未认证"
}
```

失败 (500):
```json
{
  "detail": "服务器内部错误"
}
```

---

## 附录：数据类型定义

### NodeStatus（节点状态）
- `pending`: 待审核
- `published`: 已发布
- `locked`: 已锁定（完结）
- `rejected`: 已驳回

### UserRole（用户角色）
- `admin`: 管理员
- `writer`: 普通写手
- `banned`: 被封禁

### AuthorInfo（作者信息）
```json
{
  "id": 1,
  "username": "author",
  "avatar": "https://example.com/avatar.jpg"  // 可以为 null
}
```

### StoryNodeTreeItem（树节点）
用于 `/tree` 接口，包含递归的 `children` 字段，不含 `content` 字段。

### StoryNodeRead（节点详情）
用于详情页，包含 `content` 字段，不含 `children` 字段。

### StoryNodeListItem（列表项）
用于列表展示（feed、search、user-nodes），不含 `children` 和 `content` 字段。

---

## 最小可上线版本（MVP）需要的接口

如果要快速上线，至少需要以下接口：

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

**文档版本**: 2.0  
**更新日期**: 2026-02-06  
**说明**: 本文档基于 openapi.json 自动生成，包含所有接口的详细请求和响应格式