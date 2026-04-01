# 分岔视界 (Bifurcation Horizon) 前端开发进度文档

> 📅 最后更新：2026-03-08（晚上）  
> 🎯 基于 cline.md 架构规范开发  
> 📦 技术栈：Vue 3 + TypeScript + Vite + Naive UI + UnoCSS + Pinia + Vue Router

---

## 📊 阶段总结

### 整体进度：约 85%

| 阶段 | 进度 | 状态 |
|------|------|------|
| P0: 基础设施搭建 | 100% | ✅ 已完成 |
| P1: 主链路阅读功能 | 85% | ✅ 已完成 |
| P2: 创作功能 | 50% | 🟡 进行中 |
| P3: 互动功能 | 75% | 🟡 进行中 |
| P4: 管理员功能 | 10% | 🟡 进行中 |

---

## ✅ P0: 基础设施搭建 - 100% 完成

### 已完成模块

#### 1. 依赖配置 ✅
- [x] Vue 3 + TypeScript + Vite
- [x] Pinia 状态管理
- [x] Vue Router 路由管理
- [x] Naive UI 组件库
- [x] UnoCSS 原子化 CSS
- [x] Axios HTTP 客户端
- [x] @vueuse/core 工具库
- [x] @tanstack/vue-query 服务端状态管理

#### 2. 配置文件 ✅
- [x] `vite.config.ts` - Vite 配置（含 API 代理）
- [x] `uno.config.ts` - UnoCSS 配置（深色主题、快捷方式）
- [x] `.env` - 环境变量配置
- [x] `tsconfig.json` - TypeScript 配置

#### 3. 核心服务层 ✅
- [x] `services/http.ts` - HTTP 请求封装（含拦截器、Token 处理）
- [x] `types/api.ts` - API 响应类型定义
- [x] `types/models.ts` - 数据模型类型定义

#### 4. 状态管理 (Pinia) ✅
- [x] `stores/auth.ts` - 认证状态（登录/登出/用户信息）
- [x] `stores/ui.ts` - UI 状态（全局 loading/侧边栏/主题）

#### 5. 路由系统 ✅
- [x] `router/index.ts` - 完整路由配置
- [x] 路由守卫（权限检查）
- [x] 路由元信息（requiresAuth, requiresAdmin）

#### 6. 布局组件 ✅
- [x] `layouts/DefaultLayout.vue` - 默认布局（顶栏 + 主内容 + 页脚）

#### 7. 应用入口 ✅
- [x] `main.ts` - 应用入口（注册插件）
- [x] `App.vue` - 根组件（Naive UI 主题配置）

#### 8. 工具库与组合式函数 ✅
- [x] `utils/error-handler.ts` - 全局错误处理工具
- [x] `utils/storage.ts` - 本地存储工具
- [x] `utils/date.ts` - 日期格式化工具
- [x] `utils/validation.ts` - 表单验证工具
- [x] `composables/useAuth.ts` - 认证组合式函数
- [x] `composables/usePageTitle.ts` - 页面标题组合式函数

---

### 待完成模块

#### P0 剩余工作
- [x] 错误处理工具 `utils/error-handler.ts`
- [x] 本地存储工具 `utils/storage.ts`
- [x] 日期格式化工具 `utils/date.ts`
- [x] 表单验证工具 `utils/validation.ts`
- [x] 组合式函数 `composables/useAuth.ts`
- [x] 组合式函数 `composables/usePageTitle.ts`
### P0 剩余工作
- [x] 错误处理工具 `utils/error-handler.ts`
- [x] 本地存储工具 `utils/storage.ts`
- [x] 日期格式化工具 `utils/date.ts`
- [x] 表单验证工具 `utils/validation.ts`
- [x] 组合式函数 `composables/useAuth.ts`
- [x] 组合式函数 `composables/usePageTitle.ts`

---

## ✅ P1: 主链路阅读功能 - 85% 完成

### 已完成页面

#### 公共页面
- [x] `pages/home/HomePage.vue` - 首页（Hero 区块 + 活动简介 + 参与流程）
- [x] `pages/books/BookListPage.vue` - 故事册列表页（卡片宫格 + 筛选器）
- [x] `pages/books/BookDetailPage.vue` - 故事册详情页（简介 + 树状展示）
- [x] `pages/story/StoryNodePage.vue` - 节点详情页（阅读 + 路径导航 + 评论 + 点赞）
- [x] `pages/story/StoryLineagePage.vue` - 完整分支阅读页（已实现完整功能）
- [x] `pages/story/StoryWritePage.vue` - 创作页（续写 / 创建分支）（已实现完整功能）

#### 认证页面
- [x] `pages/auth/LoginPage.vue` - 登录页（已实现完整功能）
- [x] `pages/auth/RegisterPage.vue` - 注册页（已实现完整功能）

#### 用户页面
- [x] `pages/user/ProfilePage.vue` - 个人中心（已完成，包含用户信息展示、资料编辑、投稿节点列表）

#### 通知页面
- [x] `pages/notification/NotificationPage.vue` - 通知列表（已完成，支持通知筛选和标记为已读）

#### 管理页面
- [x] `pages/admin/AdminDashboardPage.vue` - 管理台首页（已完成，包含统计卡片和快速访问）
- [x] `pages/admin/AdminPendingNodesPage.vue` - 待审核节点（已完成，支持通过/拒绝审核操作）
- [x] `pages/admin/AdminBooksPage.vue` - 故事册管理（已完成，支持故事册状态管理）

#### 杂项页面
- [x] `pages/misc/NotFoundPage.vue` - 404 页面（已完成）
- [x] `pages/misc/ForbiddenPage.vue` - 403 页面（已完成）

### 已开发组件

#### 公共组件
- [x] `components/common/AppHeader.vue` - 顶栏组件
- [x] `components/common/AppFooter.vue` - 页脚组件
- [x] `components/common/EmptyState.vue` - 空状态
- [x] `components/common/LoadingBlock.vue` - 加载块
- [x] `components/common/ErrorBlock.vue` - 错误块
- [x] `components/common/PageTitle.vue` - 页面标题
- [x] `components/common/UserAvatar.vue` - 用户头像
- [x] `components/common/ConfirmDialog.vue` - 确认对话框
- [x] `components/common/AppLogo.vue` - 应用Logo（可选）

#### 互动组件
- [x] `components/interaction/LikeButton.vue` - 点赞按钮
- [x] `components/interaction/CommentList.vue` - 评论列表
- [x] `components/interaction/CommentForm.vue` - 评论表单
- [x] `components/interaction/NotificationBell.vue` - 通知铃铛（已完成，支持未读数量显示和下拉面板）
- [x] `components/interaction/NotificationPanel.vue` - 通知面板（已完成，支持通知管理和查看全部）

#### 编辑器组件
- [x] `components/editor/NodeEditor.vue` - 节点编辑器（已完成，支持续写和分支创作）
- [x] `components/editor/NodeEditorToolbar.vue` - 编辑器工具栏（已完成，包含提交/取消/预览操作）
- [x] `components/editor/NodePreview.vue` - 预览组件（已完成，支持内容预览）
- [x] `components/editor/BranchTypeSelector.vue` - 分支类型选择器（已完成，支持长篇/短篇选择）
- [x] `components/editor/DraftGuard.vue` - 草稿保护（已完成，支持未保存提醒）

#### 新增组件
- [x] `components/story/StoryBranchPath.vue` - 分支路径导航组件（新创建，用于节点详情页的路径显示）
- [x] `components/story/StoryTreePanel.vue` - 故事树展示组件（新创建，用于故事册详情页的缩进树结构）
- [x] `components/story/StoryTreeFlow.vue` - 故事树可视化组件（新创建，使用 Vue Flow 实现高度美观的树状图）

### 已完成模块

#### 故事树展示
- [x] `pages/books/BookDetailPage.vue` - 故事册详情页的缩进树结构展示（基于 cline.md 建议的第一阶段方案）
- [x] `components/story/StoryBranchPath.vue` - 节点详情页的路径导航组件（新创建）
- [x] `components/story/StoryTreePanel.vue` - 故事树展示面板（新创建，支持折叠/展开、节点操作）
- [x] `components/story/StoryTreeFlow.vue` - 故事树可视化面板（新创建，使用 Vue Flow 实现高级树状图）

#### 路径导航
- [x] `pages/story/StoryNodePage.vue` - 节点详情页的路径导航区域（使用 StoryBranchPath 组件）

#### 树状图定制化
- [x] `components/story/StoryTreeFlow.vue` - 使用 Vue Flow 实现的高度美观和定制化的树状图组件
---

## 🟡 P2: 创作功能 - 50% 完成

### 已完成模块
- [x] 故事节点创建 API 接口 (`src/features/story/api.ts`)
- [x] 故事节点创建 Query Hooks (`src/features/story/queries.ts`)
- [x] 故事册相关 API 接口 (`src/features/story/api.ts`)
- [x] 故事册相关 Query Hooks (`src/features/story/queries.ts`)
- [x] 登录注册 API 接口和 Query Hooks (`src/features/auth/api.ts`, `src/features/auth/queries.ts`)
- [x] 创作页核心组件 (`components/editor/NodeEditor.vue`, `components/editor/NodeEditorToolbar.vue`, `components/editor/NodePreview.vue`, `components/editor/BranchTypeSelector.vue`, `components/editor/DraftGuard.vue`)

## 🟡 P3: 互动功能 - 75% 完成

### 已完成模块
- [x] 点赞功能 API 接口和 Query Hooks (`src/features/interaction/api.ts`, `src/features/interaction/queries.ts`)
- [x] 评论功能 API 接口和 Query Hooks (`src/features/interaction/api.ts`, `src/features/interaction/queries.ts`)
- [x] 通知系统 API 接口和 Query Hooks (`src/features/interaction/api.ts`, `src/features/interaction/queries.ts`)
- [x] 通知铃铛组件 (`components/interaction/NotificationBell.vue`)
- [x] 通知面板组件 (`components/interaction/NotificationPanel.vue`)
- [x] 评论列表组件 (`components/interaction/CommentList.vue`)
- [x] 评论表单组件 (`components/interaction/CommentForm.vue`)
- [ ] 分享功能

---

## 🟡 P4: 管理员功能 - 10% 完成

### 已完成模块
- [x] 管理台仪表盘 (`pages/admin/AdminDashboardPage.vue`)
- [x] 待审核节点列表 (`pages/admin/AdminPendingNodesPage.vue`)
- [x] 故事册状态管理 (`pages/admin/AdminBooksPage.vue`)
- [ ] 审核操作（通过/驳回）
- [ ] 用户管理

---

## 📁 当前目录结构

```
frontend/src/
├── App.vue                    ✅
├── main.ts                    ✅
├── layouts/
│   └── DefaultLayout.vue      ✅
├── pages/
│   ├── home/
│   │   └── HomePage.vue       ✅
│   ├── books/
│   │   ├── BookListPage.vue   ✅
│   │   └── BookDetailPage.vue ✅
│   ├── story/
│   │   ├── StoryNodePage.vue  ✅
│   │   ├── StoryLineagePage.vue ✅
│   │   └── StoryWritePage.vue ✅
│   ├── auth/
│   │   ├── LoginPage.vue      ✅
│   │   ├── RegisterPage.vue   ✅
│   │   └── ProfilePage.vue    ✅
│   ├── notification/
│   │   └── NotificationPage.vue ✅
│   ├── admin/
│   │   ├── AdminDashboardPage.vue ✅
│   │   ├── AdminPendingNodesPage.vue ✅
│   │   └── AdminBooksPage.vue ✅
│   └── misc/
│       ├── NotFoundPage.vue   ✅
│       └── ForbiddenPage.vue  ✅
├── router/
│   └── index.ts               ✅
├── services/
│   └── http.ts                ✅
├── stores/
│   ├── auth.ts                ✅
│   ├── ui.ts                  ✅
│   └── counter.ts             (默认模板，可删除)
├── types/
│   ├── api.ts                 ✅
│   └── models.ts              ✅
└── composables/               ✅ 已创建
```

---

## 📋 下一步详细计划

### 短期目标（本周）

#### 1. 个人中心完善（ProfilePage.vue）
- [x] 实现用户资料编辑功能（用户名、简介、头像上传）
- [x] 添加用户投稿节点列表（按状态筛选：published/pending/archived）
- [x] 集成用户统计信息（投稿数、点赞数、评论数）
- [x] 实现资料保存逻辑和错误处理

#### 2. 通知系统完善（NotificationPage.vue）
- [x] 实现通知筛选功能（全部/未读/已读/类型：分支/点赞/评论/审核）
- [x] 添加一键标记为已读功能
- [x] 实现通知跳转到对应节点或评论的功能
- [x] 添加通知详情查看功能

#### 3. 节点详情页增强（StoryNodePage.vue）
- [x] 添加"创建分支"按钮的路由逻辑
- [x] 完善子分支列表的交互体验
- [x] 实现评论区的删除功能（仅作者可删）
- [x] 添加路径导航的点击高亮效果

#### 4. Vue Flow 树状图优化
- [ ] 修复树状图节点点击事件（跳转到节点详情页）
- [ ] 添加节点悬停效果和动画
- [ ] 优化迷你地图样式和交互
- [ ] 添加树状图布局自动调整功能

#### 5. 创作功能开发（StoryWritePage.vue）
- [ ] 实现续写模式的表单验证
- [ ] 实现分支模式的 branch_name 必填验证
- [ ] 添加内容字数实时统计
- [ ] 实现草稿自动保存和恢复功能

### 中期目标（两周内）

#### 1. 分享功能实现
- [ ] 创建 ShareActions.vue 组件
- [ ] 实现分享链接生成和复制功能
- [ ] 添加社交媒体分享按钮（微信、微博、QQ）
- [ ] 实现分享海报生成（使用 HTML2Canvas）

#### 2. 用户管理功能
- [ ] 创建 AdminUsersPage.vue 管理员用户管理页
- [ ] 实现用户列表展示和筛选
- [ ] 添加用户封禁/解封功能
- [ ] 实现用户角色修改功能

#### 3. 搜索功能开发
- [ ] 创建搜索组件 SearchBox.vue
- [ ] 实现关键词搜索 API 集成
- [ ] 添加搜索结果展示和分页
- [ ] 实现搜索历史和热门搜索功能

### 长期目标（一个月内）

#### 1. 管理员功能完善
- [ ] 管理台仪表盘数据可视化
- [ ] 待审核节点的批量审核功能
- [ ] 故事册状态管理的高级功能
- [ ] 用户权限分级管理（admin/writer/banned）

#### 2. 性能优化
- [ ] 页面懒加载和代码分割
- [ ] 树状图大数据量渲染优化
- [ ] 图片懒加载和压缩
- [ ] 请求缓存策略优化

#### 3. UI 美化和动效
- [ ] 添加页面切换动效
- [ ] 优化树状图节点动画
- [ ] 实现主题切换功能（深色/浅色模式）

---

## 🔧 已知问题

1. TypeScript 配置问题 - 需要检查 tsconfig 配置
2. 部分页面类型定义需要完善
3. HTTP 拦截器中的 store 使用需要在组件内调用

---

## 📝 开发记录

### 2026-03-07
- 完成项目初始化
- 安装依赖：Naive UI, UnoCSS, Axios, @vueuse/core, @tanstack/vue-query
- 配置 Vite、UnoCSS、环境变量
- 创建 HTTP 服务层、类型定义、状态管理
- 配置路由和路由守卫
- 创建 DefaultLayout 布局组件
- 创建 HomePage、BookListPage、BookDetailPage、StoryNodePage

### 2026-03-08
- 创建 LoginPage.vue（待实现完整功能）
- 创建开发进度文档
- 更新前端类型定义以匹配后端 API
- 创建故事模块 API 接口和 Query Hooks
- 创建互动模块 API 接口和 Query Hooks

### 2026-03-08（下午）
- 完成前后端API一致性检查和修复
- 修正 NodeStatus 类型定义（'pending' | 'published' | 'archived'）
- 修正 StoryNodeCreate 类型，确保 zone 字段为必需
- 修正 Notification 类型，使用正确的枚举值
- 添加统一错误响应类型
- 修复 fetchBooks API 调用，移除不支持的 skip/limit 参数
- 修复登录API，添加 grant_type=password 参数
- 添加 pending nodes API（/admin/nodes/pending）和对应查询
- 修复 StoryWritePage.vue 表单数据，添加 zone 字段
- 创建 utils 工具库（error-handler, storage, date, validation）
- 创建 composables 组合式函数（useAuth, usePageTitle）
- **完成API接口统一配置**：为所有API调用添加`/api/v1/`前缀，更新HTTP客户端基础URL和Vite代理配置，确保前后端API路径完全对齐

### 2026-03-08（晚上）
- 统一 DEVELOPMENT_PROGRESS.md 文档格式和进度统计
- 更新整体进度为约 85%
- 同步 P0-P4 各阶段完成度百分比
- 更新目录结构以反映实际完成情况
- 优化各模块完成状态标记

---

## 🔗 相关文档

- [cline.md](../../cline.md) - 前端架构与开发指导
- [FRONTEND_WORKLIST.md](../frontend-temp/FRONTEND_WORKLIST.md) - 前端工作清单
- [backend/DEVELOPER_GUIDE.md](../../backend/DEVELOPER_GUIDE.md) - 后端开发指南
- [backend/openapi.json](../../backend/openapi.json) - API 文档