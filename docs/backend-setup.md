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
SSO_ADMIN_CLAIM_KEYS=roles,role,groups
SSO_ADMIN_MATCH_VALUES=admin,administrator
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

具体配置方法和 Casdoor / 上游 Provider callback 的区别，见 `docs/casdoor-callback-setup.md`。

如果你希望新用户首次通过 Casdoor 登录时自动成为本站管理员，还需要补充：

- `SSO_ADMIN_CLAIM_KEYS`
  - 后端会依次检查这些 claim，例如 `roles`、`role`、`groups`
- `SSO_ADMIN_MATCH_VALUES`
  - 只要 claim 值里包含这些标记之一，就把新建本地用户初始化为 `admin`

注意：

- 这个规则只作用于“首次创建本地用户”
- 既有本地用户的 `role` 不会在后续登录时被 Casdoor 自动覆盖

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
3. 设置管理员 SSO 绑定信息：

```env
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_AUTH_PROVIDER=casdoor
ADMIN_AUTH_SUBJECT=
ADMIN_AUTH_USER_ID=
```

4. 如果是全新库，运行 `python init_database.py`
5. 如果是旧库，运行 `python scripts/migrate_add_sso_columns.py`
6. 启动 `python main.py`
7. 访问 `/health`
8. 前端发起 `/api/v1/auth/sso/login-url`

## 7. 当前注意事项

- 日常业务接口仍然依赖本站本地 JWT
- 对外认证入口已经收敛为 SSO，不再提供本地密码 API
- 初始化脚本现在会直接创建一个绑定 SSO subject 的管理员账号
- `docs/` 才是当前有效文档来源，`backend` 目录内旧文档已清理
