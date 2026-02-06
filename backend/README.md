# Tree Story Project - Backend API

基于 FastAPI 的异步后端服务，用于树状故事续写平台。

## 📋 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [数据库](#数据库)
- [测试](#测试)
- [已知问题](#已知问题)
- [开发指南](#开发指南)

## 项目概述

这是一个多人协作的树状故事续写平台后端，支持：
- 用户注册/登录（邮箱验证码）
- 故事节点的树状结构管理
- 审核机制（管理员审核用户提交的内容）
- 点赞、评论、通知等社交互动
- 活动管理、发现功能
- 图片上传

## 技术栈

- **Web 框架**: FastAPI 0.100+
- **数据库**: MySQL + SQLAlchemy 2.0 (async)
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt (passlib)
- **数据验证**: Pydantic 2.0
- **数据库迁移**: Alembic
- **ASGI 服务器**: Uvicorn
- **邮件**: SMTP

## 项目结构

```
backend/
├── app/
│   ├── api/
│   │   ├── api.py                 # API 路由聚合
│   │   ├── deps.py                # 依赖注入
│   │   └── v1/                    # API v1 版本
│   │       ├── admin.py           # 管理员接口
│   │       ├── auth.py            # 认证接口
│   │       ├── discovery.py       # 发现功能
│   │       ├── interaction.py     # 互动功能
│   │       ├── story.py           # 故事节点管理
│   │       ├── upload.py          # 文件上传
│   │       └── users.py           # 用户管理
│   ├── core/
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   └── security.py            # 安全相关（JWT、密码）
│   ├── models/
│   │   ├── base.py                # 基础模型
│   │   ├── auth.py                # 认证相关模型
│   │   ├── interaction.py         # 互动模型
│   │   ├── story.py               # 故事节点模型
│   │   ├── story_book.py          # 故事书/活动模型
│   │   └── user.py                # 用户模型
│   ├── schemas/
│   │   ├── common.py              # 通用响应模型
│   │   ├── interaction.py         # 互动相关 Schema
│   │   ├── story.py               # 故事节点 Schema
│   │   ├── story_book.py          # 故事书 Schema
│   │   ├── token.py               # Token Schema
│   │   └── user.py                # 用户 Schema
│   └── utils/
│       ├── avatar.py              # 头像处理
│       ├── notification.py        # 通知工具
│       └── send_email_code.py     # 邮件发送
├── alembic/                       # 数据库迁移文件
├── static/                        # 静态文件
├── tests/                         # 测试文件
├── .env                           # 环境变量配置
├── alembic.ini                    # Alembic 配置
├── init_database.py               # 初始化数据库脚本
├── main.py                        # 应用入口
├── requirements.txt               # Python 依赖
└── worklist.md                    # API 功能清单
```

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+

### 安装步骤

1. **克隆项目**
```bash
cd backend
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**

复制并编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/bifurcation_db

# 安全配置（生产环境必须修改！）
SECRET_KEY=your-very-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 管理员配置
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

5. **创建数据库**
```bash
mysql -u root -p
CREATE DATABASE bifurcation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

6. **运行数据库迁移**
```bash
alembic upgrade head
```

或者使用初始化脚本：
```bash
python init_database.py
```

7. **启动服务器**
```bash
# 开发模式（带自动重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8057

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8057 --workers 4
```

8. **访问 API 文档**
- Swagger UI: http://localhost:8057/docs
- ReDoc: http://localhost:8057/redoc

## 配置说明

### 核心配置项

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DATABASE_URL` | MySQL 数据库连接字符串 | - | ✅ |
| `SECRET_KEY` | JWT 加密密钥 | GANGWAY | ✅ |
| `ALGORITHM` | JWT 算法 | HS256 | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | 10080 (7天) | ❌ |
| `ADMIN_EMAIL` | 管理员邮箱 | admin@example.com | ❌ |
| `ADMIN_USERNAME` | 管理员用户名 | admin | ❌ |
| `ADMIN_PASSWORD` | 管理员密码 | admin123 | ❌ |

### 生产环境注意事项

⚠️ **必须修改的配置：**

1. **SECRET_KEY**: 使用强随机字符串
```bash
openssl rand -hex 32
```

2. **数据库密码**: 使用强密码

3. **关闭 SQL 日志**: 修改 `app/core/database.py`
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # 生产环境关闭
    future=True
)
```

4. **邮件配置**: 配置真实的 SMTP 服务器

## API 文档

请参考worklist.md

## 常见问题

### Q: 如何重置数据库？
```bash
alembic downgrade base
alembic upgrade head
# 或
mysql -u root -p bifurcation_db < schema.sql
```

### Q: 如何创建管理员账号？
```python
# 在 Python REPL 中
from app.core.security import get_password_hash
from app.models.user import User, UserRole

admin = User(
    email="admin@example.com",
    username="admin",
    hashed_password=get_password_hash("your_password"),
    role=UserRole.ADMIN,
    is_active=True,
    is_verified=True
)
```

### Q: 邮件验证码怎么测试？
- 测试环境查看控制台输出
- 或直接使用测试验证码 `114514`

### Q: Token 过期时间如何调整？
修改 `.env` 文件中的 `ACCESS_TOKEN_EXPIRE_MINUTES`

## 许可证

[待添加]

## 联系方式

[待添加]