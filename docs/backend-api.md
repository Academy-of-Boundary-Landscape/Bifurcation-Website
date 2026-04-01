# 后端 API 文档

本文档基于当前源码整理：

- `backend/main.py`
- `backend/app/api/api.py`
- `backend/app/api/deps.py`
- `backend/app/api/v1/*.py`

## 1. 基本信息

- 服务框架：FastAPI
- 主入口：`backend/main.py`
- API 前缀：`/api/v1`
- 健康检查：`GET /health`
- 静态资源：`/static`
- 业务接口默认认证头：`Authorization: Bearer <本站 access_token>`

## 2. 当前认证模型

当前系统已经进入 SSO 迁移阶段，认证边界如下：

- Casdoor 只在登录阶段用于确认“这个人是谁”
- 后端在 `/api/v1/auth/sso/exchange` 中完成 Casdoor 身份交换
- 交换成功后，后端继续签发本站自己的 JWT
- 后续业务接口仍然只认本站后端签发的 Bearer Token

这意味着：

- `deps.py` 里的鉴权依赖仍然是本地 token 模式
- 故事、评论、通知、上传、后台管理都不直接验证 Casdoor token

## 3. 鉴权依赖

- `get_current_user`
  - 必须带合法本站 JWT
- `get_current_active_user`
  - 必须已登录且 `is_active = true`
- `get_current_admin`
  - 必须已登录且 `role = admin`
- `get_current_user_or_none`
  - 可选登录，失败时按游客处理

## 4. 路由总览

## 4.1 Health

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/health` | 否 | 健康检查 |

## 4.2 Auth

| 方法 | 路径 | 认证 | 状态 | 说明 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/auth/sso/login-url` | 否 | 使用中 | 获取 Casdoor 登录地址 |
| POST | `/api/v1/auth/sso/exchange` | 否 | 使用中 | 用 Casdoor `code` 换取本站登录态 |
| GET | `/api/v1/auth/me` | 是 | 使用中 | 获取当前登录用户信息 |
| PATCH | `/api/v1/auth/me` | 是 | 使用中 | 修改个人资料 |

## 4.3 Story

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/v1/story/books` | 管理员 | 创建活动 |
| PATCH | `/api/v1/story/books/{book_id}` | 管理员 | 更新活动 |
| GET | `/api/v1/story/books` | 否 | 获取活动列表 |
| GET | `/api/v1/story/books/{book_id}` | 否 | 获取活动详情 |
| GET | `/api/v1/story/tree` | 可选 | 获取故事树 |
| GET | `/api/v1/story/node/{node_id}/path` | 可选 | 获取节点阅读路径 |
| POST | `/api/v1/story/node` | 登录 | 提交新节点 |
| GET | `/api/v1/story/node/{node_id}` | 可选 | 获取节点详情 |
| GET | `/api/v1/story/user/{user_id}/nodes` | 可选 | 获取用户创作列表 |
| PATCH | `/api/v1/story/node/{node_id}` | 登录 | 编辑节点 |
| DELETE | `/api/v1/story/node/{node_id}` | 登录 | 软删除节点 |

## 4.4 Users

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/v1/users/{user_id}` | 否 | 公开用户主页 |

## 4.5 Interaction

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/v1/interaction/node/{node_id}/like` | 登录 | 点赞/取消点赞 |
| GET | `/api/v1/interaction/node/{node_id}/comments` | 否 | 评论列表 |
| POST | `/api/v1/interaction/node/{node_id}/comment` | 登录 | 发布评论 |
| DELETE | `/api/v1/interaction/comment/{comment_id}` | 登录 | 软删除评论 |
| GET | `/api/v1/interaction/notifications` | 登录 | 通知列表 |
| GET | `/api/v1/interaction/notifications/unread-count` | 登录 | 未读通知数 |
| PUT | `/api/v1/interaction/notifications/{notification_id}/read` | 登录 | 单条已读 |
| PUT | `/api/v1/interaction/notifications/read` | 登录 | 全部已读 |

## 4.6 Discovery

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/v1/discovery/feed` | 否 | 最新动态 |
| GET | `/api/v1/discovery/trending` | 否 | 热门节点榜 |
| GET | `/api/v1/discovery/search` | 否 | 搜索已发布节点 |

## 4.7 Admin

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/v1/admin/nodes/pending` | 管理员 | 待审核节点列表 |
| PATCH | `/api/v1/admin/nodes/{node_id}/audit` | 管理员 | 审核节点 |
| PATCH | `/api/v1/admin/users/{user_id}` | 管理员 | 更新用户状态/角色 |
| GET | `/api/v1/admin/users` | 管理员 | 用户列表 |
| GET | `/api/v1/admin/stats` | 管理员 | 仪表盘统计 |

## 4.8 Uploads

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/v1/uploads/` | 登录 | 上传图片 |

## 5. 认证相关说明

## 5.1 `/api/v1/auth/sso/login-url`

输入：

- 可选查询参数 `redirect_to`

返回：

- `authorize_url`
- `state`

说明：

- `state` 由本站后端签名
- 前端必须原样保存并带回 `/sso/exchange`
- `redirect_to` 只允许站内路径

## 5.2 `/api/v1/auth/sso/exchange`

请求体：

```json
{
  "code": "casdoor-authorization-code",
  "state": "signed-state"
}
```

返回：

```json
{
  "access_token": "local-jwt",
  "token_type": "bearer",
  "redirect_to": "/books",
  "is_new_user": false
}
```

说明：

- 后端会向 Casdoor 换取 token 并校验身份
- 后端会按 `auth_provider + auth_subject` 映射本地用户
- 如允许自动绑邮箱，且邮箱已验证，则会尝试绑定旧账号
- 最终返回的是本站自己的 token，不是 Casdoor token

## 6. 已移除的旧认证接口

以下接口已经不再保留：

- 本地注册
- 本地密码登录
- 邮箱激活占位接口
- 验证码重置密码
- 登录态改密

当前认证入口统一收敛为 SSO 登录交换。

## 7. 当前文档边界

本文档只描述当前对外可用的 API 结构，不展开所有 schema 字段和业务限制。具体规则请继续看：

- `backend-features.md`
- `casdoor-sso-migration-plan.md`
