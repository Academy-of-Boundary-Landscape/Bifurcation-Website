# Tree Story - 树状故事续写平台

多人协作的树状故事续写平台，用户可以参与故事创作，选择不同的剧情分支，共同构建宏大的故事世界。

你需要干什么：

**开发前端，按照前端文件夹里面的路线图把工作清单一项项搞定，主要代码用大模型写**

**你主要负责监工、功能测试、和外观的设计（你要是觉得颜色主题不对就吩咐ai改）**

## 🤖 AI 辅助开发指南

> 💡 **强烈推荐**: 本项目设计之初就考虑了 AI 辅助开发的最佳实践。合理使用 AI 工具（如 Cline、Copilot、Cursor 等）可以大幅提升开发效率。

### 如何使用 AI 辅助开发

#### 1. 📋 让 AI 读取工作清单

**前端开发**：
```bash
# 将前端工作清单提供给 AI
请阅读文件: frontend-temp/FRONTEND_WORKLIST.md
```

**后端开发**：
```bash
# 将后端工作清单提供给 AI
请阅读文件: backend/worklist.md
```

AI 读完工作清单后，可以：
- 帮你规划开发顺序
- 生成具体的代码结构
- 解释各个模块的依赖关系
- 提供技术栈的最佳实践建议

#### 2. 🔧 让 AI 理解项目结构

**关键步骤**：
```bash
# 让 AI 读取项目文档
请阅读:
- backend/README.md (后端架构和 API 文档)
- frontend/README.md (前端详细文档)
- frontend-temp/FRONTEND_WORKLIST.md (前端开发路线图)
- backend/worklist.md (后端功能清单)

然后总结:
1. 项目的整体架构
2. 前后端如何对接
3. 关键技术栈的使用方法
```

#### 3. 💬 与 AI 的高效对话技巧

**好的提问方式**：
```
❌ 不好: "帮我写一个登录页面"
✅ 好: "请根据 frontend-temp/FRONTEND_WORKLIST.md 的阶段四，创建一个登录页面组件。
       要求：
       1. 使用 Naive UI 的 NForm 和 NInput 组件
       2. 集成 auth.service.ts 的 login 方法
       3. 使用 auth store 管理登录状态
       4. 登录成功后跳转到首页
       5. 参考后端 API: POST /api/v1/auth/login"
```

**具体化需求**：
- 明确技术栈（Vue 3 + TypeScript + Pinia）
- 指定文件路径（创建在 src/views/auth/Login.vue）
- 关联工作清单阶段（对应 FRONTEND_WORKLIST.md 的阶段四）
- 提及 API 文档（参考 backend/README.md 的认证模块）



**阶段三：问题解决**

遇到问题时，提供：
1. 错误信息和堆栈跟踪
2. 相关代码片段
3. 工作清单中的对应阶段
4. 后端 API 文档的相关部分

例如：
"我在实现登录功能时遇到问题。错误信息是：[错误信息]。
相关代码在 src/views/auth/Login.vue 和 src/services/auth.service.ts。
我正在完成 FRONTEND_WORKLIST.md 的阶段四。
后端 API 是 POST /api/v1/auth/login。请帮我分析和解决。"


#### 4. ⚡ 快速开始示例

**给新合作者的 AI 提示词**：
```
你好，我即将开始开发 Tree Story 项目的前端。

请先阅读以下文档：
1. frontend-temp/FRONTEND_WORKLIST.md - 前端开发工作清单
2. backend/README.md - 后端 API 文档（重点看 API 文档部分）
3. frontend/README.md - 前端详细文档

然后回答：
1. 项目的整体架构是什么？
2. 前端使用哪些技术栈？
3. 我应该从哪个阶段开始开发？
4. 第一个阶段需要创建哪些文件？请列出文件路径。
5. 这些文件之间有什么依赖关系？

回答后，请根据 FRONTEND_WORKLIST.md 的阶段一，帮我创建项目的基础结构。
```

---

## 📋 目录

- [项目概述](#项目概述)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [前端开发指南](#前端开发指南)
- [后端开发指南](#后端开发指南)
- [API 文档](#api-文档)
- [贡献指南](#贡献指南)

## 项目概述

Tree Story 是一个创新的故事创作平台，核心特性包括：

- 🌳 **树状故事结构**: 用户可以续写故事，创建多个分支
- 👥 **多人协作**: 不同作者共同构建故事世界
- ✅ **审核机制**: 管理员审核用户提交的内容
- 💬 **社交互动**: 点赞、评论、通知系统
- 🏆 **活动系统**: 故事书/活动管理，主题创作
CS- 🔍 **发现功能**: Feed 流、热门榜单、搜索

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (Frontend)                      │
│  Vue 3 + TypeScript + Pinia + Naive UI + Uno-CSS            │
│                   Vite 构建工具                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              │
┌─────────────────────────────────────────────────────────────┐
│                         后端 (Backend)                       │
│                    FastAPI + SQLAlchemy                     │
│                    MySQL + Alembic                          │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

#### 前端
- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **状态管理**: Pinia
- **UI 组件库**: Naive UI
- **样式**: Uno-CSS
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **构建工具**: Vite

#### 后端
- **框架**: FastAPI
- **语言**: Python 3.8+
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0 (async)
- **认证**: JWT (python-jose)
- **数据验证**: Pydantic 2.0
- **迁移工具**: Alembic
- **ASGI 服务器**: Uvicorn

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.8+
- MySQL 8.0+
- Git

### 环境配置

#### 1. 克隆项目

```bash
git clone <repository-url>
cd bifurcation-prj
```

#### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息

# 创建数据库
mysql -u root -p
CREATE DATABASE bifurcation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8057
```

后端服务将在 `http://localhost:8057` 启动

#### 3. 前端配置

```bash
# 返回项目根目录
cd ..

cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置后端 API 地址

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

#### 4. 访问应用

打开浏览器访问 `http://localhost:5173`

## 项目结构

```
bifurcation-prj/
├── .gitignore                  # Git 忽略文件配置
├── README.md                   # 项目总文档（本文件）
├── backend/                    # 后端目录
│   ├── .env                    # 后端环境变量
│   ├── main.py                 # 后端入口文件
│   ├── requirements.txt        # Python 依赖
│   ├── alembic.ini             # Alembic 配置
│   ├── init_database.py        # 数据库初始化脚本
│   ├── README.md               # 后端详细文档
│   ├── worklist.md             # 后端功能清单
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── v1/             # API v1 版本
│   │   │   │   ├── admin.py    # 管理员接口
│   │   │   │   ├── auth.py     # 认证接口
│   │   │   │   ├── discovery.py # 发现功能
│   │   │   │   ├── interaction.py # 互动功能
│   │   │   │   ├── story.py    # 故事节点管理
│   │   │   │   ├── upload.py   # 文件上传
│   │   │   │   └── users.py    # 用户管理
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── database.py     # 数据库连接
│   │   │   └── security.py     # 安全相关
│   │   ├── models/             # 数据库模型
│   │   │   ├── user.py         # 用户模型
│   │   │   ├── story.py        # 故事节点模型
│   │   │   ├── story_book.py   # 故事书模型
│   │   │   ├── interaction.py  # 互动模型
│   │   │   └── auth.py         # 认证模型
│   │   ├── schemas/            # Pydantic Schema
│   │   ├── utils/              # 工具函数
│   │   └── static/             # 静态文件
│   ├── alembic/                # 数据库迁移文件
│   ├── tests/                  # 测试文件
│   └── venv/                   # Python 虚拟环境（不提交）
├── frontend/                   # 前端目录
│   ├── .env                    # 前端环境变量
│   ├── package.json            # Node 依赖
│   ├── vite.config.ts          # Vite 配置
│   ├── uno.config.ts           # Uno-CSS 配置
│   ├── tsconfig.json           # TypeScript 配置
│   ├── README.md               # 前端详细文档
│   ├── src/
│   │   ├── main.ts             # 前端入口
│   │   ├── App.vue             # 根组件
│   │   ├── assets/             # 静态资源
│   │   ├── components/         # 公共组件
│   │   │   ├── common/         # 通用组件
│   │   │   ├── story/          # 故事相关组件
│   │   │   ├── interaction/    # 互动组件
│   │   │   └── form/           # 表单组件
│   │   ├── composables/        # 组合式函数
│   │   ├── layouts/            # 布局组件
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── services/           # API 服务层
│   │   ├── types/              # TypeScript 类型
│   │   ├── utils/              # 工具函数
│   │   └── views/              # 页面视图
│   │       ├── auth/           # 认证页面
│   │       ├── home/           # 首页
│   │       ├── discovery/      # 发现页
│   │       ├── books/          # 活动页
│   │       ├── story/          # 故事页
│   │       ├── user/           # 用户页
│   │       ├── notification/   # 通知页
│   │       └── admin/          # 管理员页
│   └── public/                 # 公共静态文件
└── frontend-temp/              # 前端临时文件（文档、规划等）
    └── FRONTEND_WORKLIST.md    # 前端开发工作清单
```

## 前端开发指南

### 🎯 给前端开发者的快速上手指南

如果你是前端开发者，请按照以下步骤开始：

#### 第一步：了解项目

1. **阅读本 README** - 了解项目整体架构
2. **查看前端工作清单** - `frontend-temp/FRONTEND_WORKLIST.md` 包含详细的前端开发路线图
3. **熟悉后端 API** - 访问 `http://localhost:8057/docs` 查看 Swagger API 文档

#### 第二步：环境准备

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量
# 创建 .env 文件，内容如下：
VITE_API_BASE_URL=http://localhost:8057/api/v1

# 启动开发服务器
npm run dev
```

#### 第三步：理解核心概念

1. **分层架构**: View → Component → Store → Service → Backend
2. **状态管理**: 使用 Pinia 管理全局状态（用户、故事、通知等）
3. **API 调用**: 通过 Service 层统一调用后端接口
4. **路由管理**: 使用 Vue Router 进行页面导航

#### 第四步：开发流程

按照 `frontend-temp/FRONTEND_WORKLIST.md` 中的阶段进行开发：

**推荐开发顺序：**

1. **阶段一、二**: 基础设施（类型定义、API 服务层、状态管理）
2. **阶段四**: 认证模块（登录、注册）
3. **阶段三**: 公共组件（布局、通用组件）
4. **阶段五、六**: 发现和活动模块
5. **阶段七**: 故事模块（核心功能）
6. **阶段八**: 用户和通知模块
7. **阶段九**: 管理员模块
8. **阶段十**: 样式优化和性能优化

#### 第五步：使用 AI 辅助开发

参考本文档顶部的 **[AI 辅助开发指南](#-ai-辅助开发指南)** 部分，学习如何高效地使用 AI 工具加速开发。

#### 第六步：测试和调试

- 使用后端 Swagger UI 测试 API: `http://localhost:8057/docs`
- 检查浏览器控制台的 TypeScript 错误
- 测试响应式布局（移动端和桌面端）
- 验证与后端 API 的对接

### 💡 开发技巧

- **先看工作清单，再写代码**: 每个阶段都有明确的要求和目标
- **参考后端 API**: 在实现功能前，先确认后端 API 的请求和响应格式
- **使用 AI 工具**: 将工作清单和代码片段提供给 AI，让 AI 帮你生成代码
- **分步开发**: 每完成一个小功能就测试，不要一次性写太多代码
- **关注类型安全**: TypeScript 的类型系统可以帮助你提前发现错误

## 后端开发指南

后端详细文档请参考: [backend/README.md](backend/README.md)

## API 文档

### 在线文档

启动后端服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8057/docs
- **ReDoc**: http://localhost:8057/redoc

### 主要功能模块

#### 1. 认证模块 (Auth)
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/send-code-for-activation` - 发送激活验证码
- `POST /api/v1/auth/verify-email-for-activation` - 验证邮箱激活
- `POST /api/v1/auth/send-code-for-password-reset` - 发送重置密码验证码
- `POST /api/v1/auth/reset-password` - 重置密码
- `GET /api/v1/auth/me` - 获取当前用户信息
- `PATCH /api/v1/auth/me` - 更新用户信息

#### 2. 故事书模块 (StoryBook)
- `GET /api/v1/story/books` - 获取活动列表
- `POST /api/v1/story/books` - [Admin] 创建活动
- `PATCH /api/v1/story/books/{book_id}` - [Admin] 更新活动

#### 3. 故事节点模块 (StoryNode)
- `GET /api/v1/story/tree` - 获取故事树结构
- `GET /api/v1/story/node/{node_id}` - 获取节点详情
- `GET /api/v1/story/node/{node_id}/path` - 获取阅读路径
- `POST /api/v1/story/node` - 提交续写
- `PATCH /api/v1/story/node/{node_id}` - 修改节点
- `DELETE /api/v1/story/node/{node_id}` - 删除节点
- `GET /api/v1/story/user/{user_id}/nodes` - 获取用户创作列表

#### 4. 互动模块 (Interaction)
- `POST /api/v1/interaction/node/{node_id}/like` - 点赞/取消点赞
- `GET /api/v1/interaction/node/{node_id}/comments` - 获取评论列表
- `POST /api/v1/interaction/node/{node_id}/comment` - 发表评论
- `GET /api/v1/interaction/notifications` - 获取通知列表

#### 5. 发现模块 (Discovery)
- `GET /api/v1/discovery/feed` - 最新动态
- `GET /api/v1/discovery/trending` - 热门榜单
- `GET /api/v1/discovery/search` - 搜索功能

#### 6. 管理员模块 (Admin)
- `GET /api/v1/admin/nodes/pending` - 获取待审核节点
- `PATCH /api/v1/admin/nodes/{node_id}/audit` - 审核节点
- `PATCH /api/v1/admin/users/{user_id}` - 用户管理

#### 7. 上传模块 (Upload)
- `POST /api/v1/uploads/` - 上传图片

## 贡献指南

### 开发流程

1. **Fork 项目** 或创建新分支
2. **阅读工作清单**: 
   - 前端: `frontend-temp/FRONTEND_WORKLIST.md`
   - 后端: `backend/worklist.md`
3. **按照阶段开发**: 每个阶段都有明确的要求和目标
4. **使用 AI 辅助**: 参考 [AI 辅助开发指南](#-ai-辅助开发指南)
5. **编写测试**: 确保功能正常
6. **提交代码**: 写清楚的 commit message

### 代码规范

- **前端**: 遵循 Vue 3 Composition API 最佳实践
- **后端**: 遵循 FastAPI 和 PEP 8 规范
- **提交信息**: 使用清晰的描述，如 "feat: 实现登录功能" 或 "fix: 修复点赞计数错误"

### 问题反馈

如果遇到问题：
1. 检查工作清单中的对应阶段
2. 查看后端 API 文档
3. 使用 AI 工具分析和解决问题
4. 提交 Issue 时，提供详细的错误信息和复现步骤

