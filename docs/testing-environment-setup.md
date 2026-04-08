# 测试环境启动说明

本文档说明如何以测试环境端口启动项目：

- 后端：`8401`
- 前端：`5174`

当前项目已经支持通过环境变量指定测试端口，不需要再手改源码。

## 目标地址

- 前端页面：`http://127.0.0.1:5174`
- 后端健康检查：`http://127.0.0.1:8401/health`
- 前端回调页：`http://127.0.0.1:5174/auth/callback`
- 前端转发 API：`http://127.0.0.1:5174/api/v1/*` -> `http://127.0.0.1:8401/api/v1/*`

## 1. 后端测试环境

进入后端目录并激活虚拟环境：

```bash
cd /data/sunyunbo/www/Bifurcation-Website/backend
source venv/bin/activate
```

如果还没有 `.env`，先从模板复制：

```bash
cp .env.example .env
```

测试环境至少要确认这些配置：

```env
APP_ENV=dev
DEV_DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=http://127.0.0.1:5174,http://localhost:5174

CASDOOR_BASE_URL=https://auth.secret-sealing.club
CASDOOR_CLIENT_ID=你的-casdoor-client-id
CASDOOR_CLIENT_SECRET=你的-casdoor-client-secret
CASDOOR_REDIRECT_URI=http://127.0.0.1:5174/auth/callback
CASDOOR_ISSUER=https://auth.secret-sealing.club
CASDOOR_AUDIENCE=你的-casdoor-client-id

SSO_ADMIN_CLAIM_KEYS=roles,role,groups
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

初始化数据库：

```bash
python init_database.py
```

以测试端口启动后端：

```bash
BACKEND_PORT=8401 python main.py
```

启动后可检查：

```bash
curl http://127.0.0.1:8401/health
```

预期返回：

```json
{"status":"ok","service":"Tree Story Project"}
```

## 2. 前端测试环境

进入前端目录：

```bash
cd /data/sunyunbo/www/Bifurcation-Website/frontend
```

如果还没装依赖：

```bash
npm install
```

测试环境启动前，设置前端端口和后端代理目标：

```bash
VITE_PORT=5174 VITE_API_PROXY_TARGET=http://127.0.0.1:8401 npm run dev
```

启动后访问：

```text
http://127.0.0.1:5174
```

## 3. Casdoor 侧必须对应的配置

Casdoor Application 的 `Redirect URL` 必须和后端 `.env` 中的 `CASDOOR_REDIRECT_URI` 完全一致：

```text
http://127.0.0.1:5174/auth/callback
```

如果你在 Casdoor 里填的是别的域名、别的端口，登录完成后会直接回调失败。

## 4. 推荐测试路径

建议按这条路径检查：

1. 打开 `http://127.0.0.1:5174/books`
2. 点进一本书
3. 点击树节点进入正文页
4. 从节点页发起 `沿此续写` 或 `创建分支`
5. 完成 Casdoor 登录
6. 提交节点，确认节点页显示“待审核”
7. 用管理员账号登录后台审核页
8. 审核通过后，回到前台确认节点可见

## 5. 当前测试环境注意事项

- 如果你改用 `localhost`，那 `CASDOOR_REDIRECT_URI` 和 `CORS_ORIGINS` 也要一起改成 `localhost`，不要和 `127.0.0.1` 混用。
- 后端管理员身份默认来自 Casdoor claim，不再要求手工预创建本地管理员。
- 如果 Casdoor 管理员登录后没有获得本地 `admin` 角色，优先检查：
  - `SSO_ADMIN_CLAIM_KEYS`
  - `SSO_ADMIN_MATCH_VALUES`
  - Casdoor token 里是否真的带了对应 claim
