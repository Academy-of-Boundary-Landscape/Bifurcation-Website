# 后端启动与配置

## 1. 开发环境

按项目约定，后端开发使用：

- 目录：`/backend`
- 虚拟环境：`/backend/venv`

启动方式：

```bash
cd backend
source venv/bin/activate
python main.py
```

## 2. 依赖

当前关键依赖包括：

- FastAPI
- SQLAlchemy Async
- Pydantic Settings
- python-jose
- passlib
- httpx

如果需要重新安装：

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## 3. 数据库配置

项目按环境切库：

- `APP_ENV=dev`
  - 使用 `DEV_DATABASE_URL`
- `APP_ENV=prod`
  - 使用 `DATABASE_URL`

默认开发值在 `config.py` 中仍可回退到本地 sqlite。

## 4. SSO 相关环境变量

当前 Casdoor 相关配置已经接入后端：

```env
CASDOOR_BASE_URL=https://auth.secret-sealing.club
CASDOOR_CLIENT_ID=
CASDOOR_CLIENT_SECRET=
CASDOOR_APPLICATION_NAME=
CASDOOR_REDIRECT_URI=
CASDOOR_SCOPE=openid profile email
CASDOOR_AUTHORIZE_URL=
CASDOOR_TOKEN_URL=
CASDOOR_USERINFO_URL=
CASDOOR_JWKS_URL=
CASDOOR_ISSUER=
CASDOOR_AUDIENCE=
SSO_STATE_EXPIRE_MINUTES=10
SSO_AUTO_LINK_BY_EMAIL=true
SSO_ADMIN_CLAIM_KEYS=roles,role
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

另外，如果你不想在开发时看到大量 SQLAlchemy / SQLite 原始 SQL 日志，可以设置：

```env
SQL_ECHO=false
```

需要临时排查数据库行为时，再改成：

```env
SQL_ECHO=true
```

最少必须补齐：

- `CASDOOR_CLIENT_ID`
- `CASDOOR_CLIENT_SECRET`
- `CASDOOR_REDIRECT_URI`
- `CASDOOR_ISSUER`
- `CASDOOR_AUDIENCE`

`CASDOOR_REDIRECT_URI` 在这个项目里不是后端地址，而是前端回调页的绝对 URL，例如：

```env
CASDOOR_REDIRECT_URI=https://你的前端域名/auth/callback
```

具体配置方法和 Casdoor / 上游 Provider callback 的区别，见 [`casdoor-callback.md`](casdoor-callback.md)。

说明：

- 如果不手动覆盖 `CASDOOR_JWKS_URL` / `CASDOOR_ISSUER`，后端现在会优先按 `CASDOOR_APPLICATION_NAME` 推导 Casdoor 的 application-specific OIDC 路径
- 没填 `CASDOOR_APPLICATION_NAME` 时，才会回退到 Casdoor 的全局 `issuer` / `jwks` 路径

如果你希望新用户首次通过 Casdoor 登录时自动成为本站管理员，还需要补充：

- `SSO_ADMIN_CLAIM_KEYS`
  - 后端会依次检查这些 claim，当前建议直接使用 `roles`，兼容保留 `role`
- `SSO_ADMIN_MATCH_VALUES`
  - 只要 claim 值里包含这些标记之一，就把新建本地用户初始化为 `admin`

当前建议：

- 在 Casdoor 里给管理员用户分配角色，例如 `admin`
- 确保该角色会出现在 token / userinfo 的 `roles` claim 中
- 后端 `.env` 使用：

```env
SSO_ADMIN_CLAIM_KEYS=roles,role
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

不建议默认依赖 `groups`：

- 目前项目后端的管理员判断只需要一个稳定的“是否管理员”信号
- Casdoor 官方文档更明确的概念是 token claims、roles、permissions
- 对这个站点来说，用角色判断后台权限比用权限列表或自定义组字段更直接、更易维护

注意：

- 新建用户会按这些 claim 初始化角色
- 后续 SSO 登录时，后端也会继续按 claim 同步 `admin/writer` 角色
- `banned` 仍由本站本地控制，不会被 Casdoor 自动解除封禁

## 5. 数据库补列脚本

如果你是全新数据库，直接运行 `python init_database.py` 即可。

只有在“已经存在旧版数据库结构”的情况下，才需要下面这个补列脚本。

现阶段提供了临时脚本：

```bash
cd backend
source venv/bin/activate
python scripts/migrate_add_sso_columns.py
```

这个脚本会补齐：

- `auth_provider`
- `auth_subject`
- `auth_user_id`
- `auth_last_sync_at`

以及对应索引和唯一约束索引。

## 6. 当前启动前检查

建议按这个顺序：

1. 激活 `backend/venv`
2. 检查 `.env` 是否补齐数据库与 Casdoor 配置
3. 如果你确实要预绑定一个管理员账号，再设置管理员 SSO 绑定信息：

```env
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_AUTH_PROVIDER=casdoor
ADMIN_AUTH_SUBJECT=
ADMIN_AUTH_USER_ID=
```

4. 如果是全新库，运行 `python init_database.py`
5. 如果是旧库，运行 `python scripts/migrate_add_sso_columns.py`
6. 按需设置 `BACKEND_HOST` / `BACKEND_PORT`，例如测试环境可设为 `8401`
7. 启动 `python main.py`
8. 访问 `/health`
9. 前端发起 `/api/v1/auth/sso/login-url`

说明：

- `init_database.py` 只会在显式提供 `ADMIN_AUTH_SUBJECT` 时预创建管理员账号
- 如果未提供 `ADMIN_AUTH_SUBJECT`，初始化脚本会跳过管理员预创建
- 当前推荐方式是让 Casdoor 中带管理员 claim 的用户首次登录，由 SSO 同步逻辑自动创建或同步为本地管理员

## 7. 当前注意事项

- 日常业务接口仍然依赖本站本地 JWT
- 对外认证入口已经收敛为 SSO，不再提供本地密码 API
- 初始化脚本默认不会强制创建管理员账号；管理员通常来自 Casdoor 登录时的 claim 同步
- `docs/` 才是当前有效文档来源，`backend` 目录内旧文档已清理

## 8. 测试环境启动（端口 8401 / 5174）

测试环境与开发环境使用不同端口以便同时运行，互不干扰。

目标地址：

- 前端：`http://127.0.0.1:5174`
- 后端健康检查：`http://127.0.0.1:8401/health`
- 前端代理：`http://127.0.0.1:5174/api/v1/*` → `http://127.0.0.1:8401/api/v1/*`

### 测试后端

`.env` 关键项（`CASDOOR_REDIRECT_URI` 指向测试前端端口）：

```env
APP_ENV=dev
DEV_DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=http://127.0.0.1:5174,http://localhost:5174
CASDOOR_REDIRECT_URI=http://127.0.0.1:5174/auth/callback
```

```bash
cd backend
source venv/bin/activate
python init_database.py         # 仅首次
BACKEND_PORT=8401 python main.py
```

### 测试前端

Vite 在 `VITE_PORT=5174` 时自动将代理目标推断为 `8401`：

```bash
cd frontend
VITE_PORT=5174 npm run dev
```

### Casdoor 侧配置

Casdoor Application 的 `Redirect URL` 必须和后端 `.env` 中的 `CASDOOR_REDIRECT_URI` 完全一致：

```
http://127.0.0.1:5174/auth/callback
```

`127.0.0.1` 和 `localhost` 不可混用，`CORS_ORIGINS` 也需保持一致。

### 推荐测试路径

1. 访问 `http://127.0.0.1:5174/books`
2. 进入一本书，点击树节点
3. 从节点页发起续写，完成 Casdoor 登录
4. 提交节点，确认显示"待审核"
5. 管理员登录后台审核，审核通过后确认节点可见
