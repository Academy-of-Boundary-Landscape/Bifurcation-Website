# Bifurcation — 树状故事续写平台

多人协作的树状故事续写平台。用户可以参与故事创作，选择不同的剧情分支，共同构建宏大的故事世界。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Pinia + Naive UI + UnoCSS + Vite |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) + Pydantic 2 |
| 数据库 | PostgreSQL（生产）/ SQLite（开发） |
| 认证 | Casdoor SSO（OAuth 2.0）+ 本站本地 JWT 会话 |
| 运行时 | Python 3.13 / Node.js 18+ |

## 项目结构

```
.
├── backend/
│   ├── main.py                  # 入口，读取 BACKEND_HOST / BACKEND_PORT
│   ├── init_database.py         # 全新库初始化脚本
│   ├── requirements.txt
│   ├── .env.example             # 环境变量模板
│   ├── app/
│   │   ├── api/v1/              # 路由：auth / story / interaction / discovery / admin / upload
│   │   ├── core/                # config / database / security
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic schema
│   │   └── services/            # 业务逻辑层
│   ├── scripts/
│   │   └── migrate_add_sso_columns.py  # 旧库补列脚本（新库不需要）
│   ├── static/uploads/          # 上传图片存放目录
│   └── tests/                   # 后端单元测试
├── frontend/
│   ├── src/
│   │   ├── features/            # API 调用层（按功能模块）
│   │   ├── pages/               # 页面组件
│   │   ├── components/          # 通用组件
│   │   ├── stores/              # Pinia store
│   │   ├── router/              # 路由 + 权限守卫
│   │   └── types/               # TypeScript 类型定义
│   └── vite.config.ts           # 读取 VITE_PORT / VITE_API_PROXY_TARGET
└── docs/                        # 项目文档（见 docs/README.md）
```

---

## 开发环境启动

默认端口：后端 `8057`，前端 `5173`。

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env，至少填写：
#   SECRET_KEY / CASDOOR_CLIENT_ID / CASDOOR_CLIENT_SECRET /
#   CASDOOR_REDIRECT_URI / CASDOOR_ISSUER / CASDOOR_AUDIENCE

python init_database.py         # 初始化数据库（仅首次）
python main.py
```

健康检查：`curl http://localhost:8057/health`

Swagger UI：`http://localhost:8057/docs`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`。

前端通过 Vite 代理把 `/api/v1/*` 转发到后端，无需额外配置。

---

## 测试环境启动

测试环境与开发环境隔离，使用不同端口：后端 `8401`，前端 `5174`。

### 后端（测试端口）

`.env` 中至少确认以下配置（`CASDOOR_REDIRECT_URI` 指向测试前端）：

```env
APP_ENV=dev
DEV_DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=http://127.0.0.1:5174,http://localhost:5174

CASDOOR_BASE_URL=https://auth.example.com
CASDOOR_CLIENT_ID=your-client-id
CASDOOR_CLIENT_SECRET=your-client-secret
CASDOOR_REDIRECT_URI=http://127.0.0.1:5174/auth/callback
CASDOOR_ISSUER=https://auth.example.com
CASDOOR_AUDIENCE=your-client-id

SSO_ADMIN_CLAIM_KEYS=roles,role
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

```bash
python init_database.py
BACKEND_PORT=8401 python main.py
```

### 前端（测试端口）

Vite 会自动把代理目标推断为 `8401`（当 `VITE_PORT=5174` 时）：

```bash
VITE_PORT=5174 npm run dev
```

或者显式指定代理目标：

```bash
VITE_PORT=5174 VITE_API_PROXY_TARGET=http://127.0.0.1:8401 npm run dev
```

访问 `http://127.0.0.1:5174`。

> **注意**：Casdoor Application 的 `Redirect URL` 必须和 `CASDOOR_REDIRECT_URI` 完全一致，包括域名和端口。`127.0.0.1` 和 `localhost` 不可混用。

---

## 生产部署

### 准备工作

1. 准备 PostgreSQL 数据库：

```sql
CREATE USER bifurcation WITH PASSWORD 'your-password';
CREATE DATABASE bifurcation_db OWNER bifurcation;
GRANT ALL PRIVILEGES ON DATABASE bifurcation_db TO bifurcation;
```

2. 在 Casdoor 创建 Application，将 `Redirect URL` 设为：

```
https://your-domain.com/auth/callback
```

### 后端

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

生产 `.env`（关键项）：

```env
APP_ENV=prod
DATABASE_URL=postgresql+asyncpg://bifurcation:your-password@localhost:5432/bifurcation_db
SECRET_KEY=一个至少64字符的随机字符串
CORS_ORIGINS=https://your-domain.com
SQL_ECHO=false

CASDOOR_BASE_URL=https://auth.your-casdoor.com
CASDOOR_CLIENT_ID=your-client-id
CASDOOR_CLIENT_SECRET=your-client-secret
CASDOOR_REDIRECT_URI=https://your-domain.com/auth/callback
CASDOOR_ISSUER=https://auth.your-casdoor.com
CASDOOR_AUDIENCE=your-client-id

SSO_ADMIN_CLAIM_KEYS=roles,role
SSO_ADMIN_MATCH_VALUES=admin,administrator
```

初始化数据库（仅首次）：

```bash
python init_database.py
```

> 如果是从旧版本升级（已有数据库但缺少 SSO 字段），改用：
> `python scripts/migrate_add_sso_columns.py`

启动服务（建议用 systemd 或 supervisor 管理进程）：

```bash
BACKEND_HOST=127.0.0.1 BACKEND_PORT=8057 python main.py
```

或者用 uvicorn 直接启动：

```bash
uvicorn main:app --host 127.0.0.1 --port 8057 --workers 2
```

### 前端

```bash
cd frontend
npm install
npm run build        # 产物在 frontend/dist/
```

### Nginx 配置参考

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    # SSL 证书配置...

    root /path/to/frontend/dist;
    index index.html;

    # 前端 SPA：未知路由回退到 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反代到后端
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8057;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件静态服务（由后端直接 serve）
    location /static/ {
        proxy_pass http://127.0.0.1:8057;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

### 管理员账号

无需手动创建。让 Casdoor 中拥有 `admin` 角色的用户首次 SSO 登录，后端会自动同步并赋予本地 `admin` 权限。

---

## 运行测试

```bash
cd backend
source venv/bin/activate
python -m unittest discover -s tests
```

测试使用 SQLite 内存库，不依赖真实 Casdoor 或 PostgreSQL。

---

## 文档

详细文档见 [`docs/`](docs/README.md)，分为 `docs/backend/` 和 `docs/frontend/` 两个子目录，涵盖架构、API、业务规则、数据层、视觉规范等。
