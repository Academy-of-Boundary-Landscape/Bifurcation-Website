# Casdoor SSO 登录迁移评审与实施方案

> 说明：这份文档主要保留迁移背景、历史评审和后续规划。其中第 2、7、9 节包含迁移前状态与未完成项，不应直接视为当前代码现状。当前实现请优先以 `backend-setup.md`、`backend-api.md`、`backend-features.md` 为准。

## 1. 结论

当前后端不适合直接切成“纯第三方 token 驱动”的模式，原因是业务代码广泛依赖本地 `users` 表和本地 `User.id`。

推荐方案：

- Casdoor 负责登录、注册、找回密码、统一身份认证
- 本站后端保留本地 `users` 表，作为业务画像和权限层
- 前端完成 Casdoor OAuth/OIDC 登录
- 后端新增一个 `sso exchange` 流程，把 Casdoor 身份映射为本站本地用户
- 后端继续签发本站自己的 JWT，现有业务接口基本不用重写

这条路线可以达到你的目标：“不再自己实现登录逻辑”，同时控制改动范围。

## 2. 当前后端现状

### 2.1 认证强绑定本地 JWT

- `backend/app/api/deps.py` 当前直接用 `SECRET_KEY` 解本站 JWT，并把 `sub` 当作本地 `users.id`
- `get_current_active_user`、`get_current_admin`、`get_current_user_or_none` 都依赖这个逻辑
- `story`、`interaction`、`upload`、`admin` 等模块都通过这些依赖拿本地 `User`

这意味着如果你直接让业务接口去吃 Casdoor token，就必须整体改造依赖层和权限判断。

### 2.2 认证接口仍是“站内账号体系”

- `backend/app/api/v1/auth.py` 里 `register` 直接创建本地用户并写入 `hashed_password`
- `login` 用邮箱/用户名 + 密码校验本地密码，再签发本地 JWT
- `change-password`、`reset-password` 仍是本地密码体系
- 邮箱激活接口已经是占位实现，但文档还在描述完整验证码注册流程

### 2.3 用户表不是纯认证表，而是业务核心表

`backend/app/models/user.py` 里的 `users` 表不仅保存登录标识，还被大量业务表引用：

- 故事节点作者
- 评论作者
- 点赞用户
- 通知收发人
- 管理员角色判断

因此不能因为接入 Casdoor 就删除本地用户表。

## 3. 文档与代码的主要冲突

以下文档目前不应再作为认证设计依据：

- `backend/README.md`
- `backend/worklist.md`
- `backend/DEVELOPER_GUIDE.md`
- `backend/app/api/v1/API_SUMMARY.md`

主要冲突：

- 文档写“邮箱验证码注册”，但代码里激活接口是占位
- 文档写“完整注册激活流程”，但实际 `register` 直接注册成功
- 文档把认证描述为稳定方案，但当前实现其实仍是过渡期本地账号体系

后续与登录迁移相关的文档应统一收敛到 `/docs`。

## 4. 推荐目标架构

### 4.1 设计原则

- 身份认证交给 Casdoor
- 本站保留本地权限和画像
- 对现有业务接口保持兼容
- 优先减少一次性重构

### 4.2 推荐登录流

建议使用 OIDC Authorization Code + PKCE。

流程如下：

1. 前端跳转到 Casdoor 登录页
2. 用户在 `auth.secret-sealing.club` 完成登录/注册
3. Casdoor 回调到前端页面，前端拿到 `code`
4. 前端把 `code` 发给本站后端的 `POST /api/v1/auth/sso/exchange`
5. 后端向 Casdoor token endpoint 换取 token，并校验 `issuer`、`audience`、签名和过期时间
6. 后端根据 Casdoor 用户唯一标识查找或创建本地用户
7. 后端签发本站现有格式的 JWT 给前端
8. 前端后续仍用 `Authorization: Bearer <本站JWT>` 访问业务接口

这样改完后：

- 登录/注册/忘记密码不再由本站实现
- 现有 `deps.py` 可基本保持不变
- 业务接口不需要全面替换成 Casdoor token 验证

## 5. 不推荐的第一阶段方案

### 5.1 不建议直接让所有业务接口验证 Casdoor token

虽然理论上可行，但对你当前项目不划算。

原因：

- `deps.py` 要整体改写为 OIDC/JWKS 校验
- token claim 到本地用户的映射要重做
- Swagger OAuth2 配置、可选登录依赖、管理员鉴权都会一起受影响
- 所有依赖本地 `sub=user.id` 的地方都要重新审视

这更适合系统已经稳定后再做二阶段收敛。

## 6. 数据模型建议

为本地 `users` 表新增 SSO 映射字段，避免再以邮箱作为唯一外部身份标识。

建议新增字段：

- `auth_provider`: `casdoor`
- `auth_subject`: Casdoor/OIDC `sub`
- `auth_user_id`: Casdoor 用户 ID，如果返回中可稳定取得
- `auth_last_sync_at`

约束建议：

- `unique(auth_provider, auth_subject)`

现有字段处理建议：

- `email` 保留，来自 Casdoor 用户资料同步
- `username` 保留，作为站内唯一名；首次登录时自动生成，之后允许站内修改
- `hashed_password` 改为允许为空
- `last_login_at` 在每次 SSO 成功后更新

## 7. 后端改造清单

### 7.1 配置项改造

把 Casdoor 相关配置放进 `.env`，至少需要：

```env
CASDOOR_BASE_URL=https://auth.secret-sealing.club
CASDOOR_CLIENT_ID=
CASDOOR_CLIENT_SECRET=
CASDOOR_ORGANIZATION_NAME=
CASDOOR_APPLICATION_NAME=
CASDOOR_REDIRECT_URI=
CASDOOR_FRONTEND_CALLBACK_URL=
CASDOOR_BACKEND_CALLBACK_URL=
CASDOOR_SCOPE=openid profile email
CASDOOR_JWKS_URL=
CASDOOR_ISSUER=
CASDOOR_AUDIENCE=
```

如果你采用“前端拿 `code`，后端 exchange”的模式，最关键的是：

- `CASDOOR_BASE_URL`
- `CASDOOR_CLIENT_ID`
- `CASDOOR_CLIENT_SECRET`
- `CASDOOR_REDIRECT_URI`
- `CASDOOR_ISSUER`
- `CASDOOR_AUDIENCE`

### 7.2 新增后端模块

建议新增：

- `backend/app/services/sso.py`
- `backend/app/schemas/sso.py`

职责拆分：

- 生成 Casdoor authorize URL
- 用授权码换 token
- 校验 Casdoor ID token 或 access token
- 解析用户 claims
- 同步或创建本地用户

### 7.3 Auth API 重构

建议新增接口：

- `GET /api/v1/auth/sso/login-url`
- `POST /api/v1/auth/sso/exchange`
- `POST /api/v1/auth/logout`

建议废弃接口：

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/send-code-for-activation`
- `POST /api/v1/auth/verify-email-for-activation`
- `POST /api/v1/auth/send-code-for-password-reset`
- `POST /api/v1/auth/change-password`
- `POST /api/v1/auth/reset-password`

其中第一阶段可以先“保留但标记 deprecated”，避免前端联调期间一次性断掉。

### 7.4 本地用户同步策略

首次 SSO 登录：

- 按 `(auth_provider, auth_subject)` 查用户
- 查不到则尝试按邮箱匹配历史账号
- 若邮箱命中旧账号，则补齐 SSO 映射字段
- 若邮箱也未命中，则创建新本地用户

同步字段建议：

- `email`
- `display_name`
- `avatar`
- `last_login_at`

不建议每次覆盖：

- `username`
- `bio`
- 本站管理角色

### 7.5 管理员角色策略

不要把 Casdoor 的普通登录身份直接等同于站内管理员。

推荐：

- 本站管理员仍由本地 `User.role=admin` 控制
- Casdoor 只负责确认“这个人是谁”
- 是否有后台权限，仍在本站数据库里判断

这样最符合你当前 `admin.py` 的设计。

## 8. 前端改造清单

前端需要把当前“本地表单登录/注册”替换成“跳转 Casdoor”。

建议：

1. 删除或隐藏原有邮箱密码登录/注册页
2. 增加 `Login with SSO` 入口
3. 新增 OAuth 回调页，例如 `/auth/callback`
4. 回调页把 `code`、`state` 发给后端 `/api/v1/auth/sso/exchange`
5. 后端返回本站 JWT 后，前端仍按现有方式存储 token 并请求 `/auth/me`

这样前端鉴权状态管理改动会最小。

## 9. 迁移实施顺序

### Phase 1: 兼容接入

- 新增 Casdoor 配置项
- 给 `users` 表增加 SSO 映射字段
- 新增 `sso.py` 服务层
- 增加 `/auth/sso/login-url` 和 `/auth/sso/exchange`
- 前端接入 Casdoor 登录入口和回调页
- 登录后继续换取本站 JWT

目标：

- 新用户只走 Casdoor
- 老业务接口完全兼容

### Phase 2: 收口旧认证能力

- 前端移除本地密码注册/登录入口
- 后端把旧认证接口标记 deprecated 或返回 410/400
- 停止使用验证码和本地密码重置逻辑

### Phase 3: 清理本地密码体系

- 删除或冻结以下代码路径：
  - 本地注册
  - 本地登录
  - 本地重置密码
  - 邮件验证码表和相关逻辑
- 将 `hashed_password` 变为 nullable
- 清理 README 和 API 文档中的旧认证描述

## 10. 迁移风险

### 10.1 用户合并风险

如果老站已有本地账号，而 Casdoor 登录后邮箱相同但并非同一人，会有误绑定风险。

建议：

- 只在邮箱已验证的前提下允许自动合并
- 保留一段时间的审计日志
- 对管理员账号禁用自动邮箱合并，必须手工绑定

### 10.2 用户名冲突

Casdoor 返回的用户名未必满足本站唯一约束。

建议：

- 首次创建本地用户时自动生成可用用户名
- 例如 `name`, `name_2`, `name_3`
- 不要把外部用户名直接强写进本地唯一字段

### 10.3 登出语义

如果只清本站 JWT 而不登出 Casdoor，用户可能会“秒登录”。

需要明确两种登出：

- 仅退出本站
- 同时退出 Casdoor

### 10.4 依赖配置不全

目前你只确定了域名 `auth.secret-sealing.club`。真正接入前还必须确认：

- client id
- client secret
- issuer
- redirect uri
- scope
- Casdoor 返回的用户唯一字段

这些都可以保留为 `.env`，但开发前必须先定值。

## 11. 建议的近期执行项

按优先级建议你先做这 6 件事：

1. 在 Casdoor 中创建这个站点对应的 application
2. 确认 redirect URI 和前端回调地址
3. 确认 token 校验需要的 `issuer`、`audience`、`jwks`
4. 给本地 `users` 表设计 SSO 映射字段
5. 先实现 `/auth/sso/exchange`
6. 前端回调页联调成功后，再下线旧登录接口

## 12. 我对这个项目的具体建议

对于这个仓库，最稳的落地方式不是“把 Casdoor token 直接灌进所有业务接口”，而是：

- 保留本地 `User`
- 保留本地角色
- 保留本地 JWT
- 删掉本地密码登录注册逻辑
- 用 Casdoor 作为唯一身份入口

如果你下一步要我继续做实现，我建议按这个顺序直接改代码：

1. 增加用户表 SSO 字段和迁移
2. 增加 Casdoor 配置
3. 写后端 SSO exchange 服务
4. 改前端登录入口和回调页
5. 最后废弃本地密码接口
