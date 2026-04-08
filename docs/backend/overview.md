# 后端概览

## 1. 目录结构

后端代码位于 `backend/`，核心结构如下：

- `backend/main.py`
  - FastAPI 应用入口
- `backend/app/api/`
  - 路由与鉴权依赖
- `backend/app/core/`
  - 配置、数据库、安全工具
- `backend/app/models/`
  - SQLAlchemy 模型
- `backend/app/schemas/`
  - Pydantic 请求/响应模型
- `backend/app/services/`
  - 服务层逻辑，已开始承接 SSO、故事节点与互动主链路
- `backend/app/utils/`
  - 邮件、通知、头像等辅助工具
- `backend/scripts/`
  - 一次性或运维辅助脚本

## 2. 关键文件

建议优先熟悉这些文件：

- `backend/main.py`
- `backend/app/api/api.py`
- `backend/app/api/deps.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/story.py`
- `backend/app/api/v1/interaction.py`
- `backend/app/api/v1/admin.py`
- `backend/app/models/user.py`
- `backend/app/models/story.py`
- `backend/app/services/sso.py`

## 3. 分层职责

## 3.1 API 层

API 层负责：

- 参数接收
- 依赖注入
- HTTP 错误码
- 调用模型或服务层

当前 API 层仍然偏重，但“创建节点 / 审核节点 / 点赞 / 评论创建”已经开始下沉到 service 层，后续整理应延续这个方向，而不是继续把新规则直接堆回路由文件。

## 3.2 Core 层

Core 层负责：

- `config.py`
  - 统一读取环境变量
- `database.py`
  - 异步数据库连接与 session
- `security.py`
  - 本地 JWT 与密码工具

## 3.3 Models 层

Models 层负责数据库实体定义，核心实体包括：

- `User`
- `StoryBook`
- `StoryNode`
- `StoryComment`
- `Notification`

## 3.4 Services 层

当前 `services/` 里最重要的是：

- `sso.py`
  - 生成 Casdoor 登录地址
  - 验证 `state`
  - 交换授权码
  - 校验 Casdoor 身份
  - 同步本地用户
- `story_nodes.py`
  - 创建故事节点
  - 处理父节点约束、根节点规则、子节点计数与审核状态切换
- `interactions.py`
  - 处理点赞/取消点赞
  - 处理评论创建、评论计数与互动通知

这意味着后端已经从“纯 route 驱动”进入“逐步建立 service 层”的阶段，后续应继续把高规则密度链路往这里收，而不是做整体性重构。

## 4. 当前认证边界

后端采用“两段式认证”：

- 外部身份确认：Casdoor
- 站内会话与权限：本地 JWT + 本地 `users` 表

因此不要把以下两类概念混在一起：

- Casdoor token
  - 只用于登录交换阶段
- 本站 JWT
  - 用于故事、互动、上传、后台管理等所有日常业务接口

## 5. 当前技术债

后端目前最明显的整理方向：

- 很多业务逻辑仍直接写在路由文件里
- service 层已经起步，但 `update/delete` 这类修改型接口还没有完全收口
- 正式 Alembic 迁移体系尚未接上当前模型维护节奏
- SSO 已经成为唯一对外登录入口，但测试与迁移体系仍需补强
- 测试文件和历史文档已经存在断层，需要逐步重建

## 6. 当前文档对应关系

如果你要继续维护后端，建议这样看文档：

- 想看结构：`backend-overview.md`
- 想看怎么启动：`backend-setup.md`
- 想看接口：`backend-api.md`
- 想看业务规则：`backend-features.md`
- 想看 SSO 迁移背景：`casdoor-sso-migration-plan.md`
