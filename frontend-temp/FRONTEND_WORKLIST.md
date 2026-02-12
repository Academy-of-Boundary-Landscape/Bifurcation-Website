# Tree Story - 前端开发工作清单

> 📋 前端开发路线图和结构指南
> 
> 技术栈: Vue 3 + TypeScript + Pinia + Naive UI + Uno-CSS
> 
> 后端 API: http://localhost:8057

---

## 📁 项目结构设计

```
frontend/
├── src/
│   ├── assets/              # 静态资源
│   │   ├── images/
│   │   └── styles/         # 全局样式
│   ├── components/         # 公共组件
│   │   ├── common/         # 通用组件（Header, Footer, Loading等）
│   │   ├── story/         # 故事相关组件（Tree, NodeCard等）
│   │   ├── interaction/   # 互动组件（Like, Comment等）
│   │   └── form/         # 表单组件（Login, Register等）
│   ├── composables/        # 组合式函数（复用逻辑）
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── useNotification.ts
│   ├── layouts/           # 布局组件
│   │   ├── DefaultLayout.vue
│   │   ├── AuthLayout.vue
│   │   └── AdminLayout.vue
│   ├── router/            # 路由配置
│   │   └── index.ts
│   ├── stores/            # Pinia 状态管理
│   │   ├── auth.ts        # 认证状态
│   │   ├── user.ts        # 用户状态
│   │   ├── story.ts        # 故事状态
│   │   ├── notification.ts  # 通知状态
│   │   └── app.ts        # 应用全局状态
│   ├── services/           # API 服务层（对应后端模块）
│   │   ├── api.ts         # Axios 配置和拦截器
│   │   ├── auth.service.ts
│   │   ├── user.service.ts
│   │   ├── story.service.ts
│   │   ├── book.service.ts
│   │   ├── interaction.service.ts
│   │   ├── discovery.service.ts
│   │   ├── admin.service.ts
│   │   └── upload.service.ts
│   ├── types/             # TypeScript 类型定义
│   │   ├── api.ts        # API 响应类型
│   │   ├── models.ts     # 数据模型类型
│   │   └── index.ts
│   ├── utils/             # 工具函数
│   │   ├── request.ts     # 请求工具
│   │   ├── storage.ts     # 本地存储
│   │   └── validation.ts  # 表单验证
│   ├── views/             # 页面视图
│   │   ├── auth/         # 认证页面
│   │   ├── home/         # 首页
│   │   ├── discovery/    # 发现页（Feed, Trending, Search）
│   │   ├── books/        # 活动页
│   │   ├── story/        # 故事页（阅读、续写）
│   │   ├── user/         # 用户页
│   │   ├── notification/ # 通知页
│   │   └── admin/        # 管理员页
│   ├── App.vue
│   └── main.ts
├── .env                  # 环境变量
├── package.json
├── uno.config.ts          # Uno-CSS 配置
└── vite.config.ts
```

---

## 🎯 核心架构原则

### 分层架构
```
View（视图层）
    ↓
Component（组件层）
    ↓
Store（状态层 - Pinia）
    ↓
Service（服务层 - API 调用）
    ↓
Backend（后端 API）
```

### 技术栈职责
- **Vue 3**: 视图和组件渲染
- **TypeScript**: 类型安全
- **Pinia**: 状态管理和数据共享
- **Naive UI**: UI 组件库
- **Uno-CSS**: 样式和布局
- **Axios**: HTTP 请求
- **Vue Router**: 路由和导航

### 前端设计风格

- 美术风格请采用深色主题，棱角锐利的科幻风格，配色以白色和紫色为主，整体风格现代、简洁，具有未来感。
- 尽量采用 Naive-UI的组件，避免自己重复造轮子
- 同上，尽可能采用Uno-CSS的原子类，避免写又臭又长的css代码


---

## 📋 开发阶段和工作清单

### 阶段一：项目初始化（基础建设）

#### 1.1 创建项目脚手架
- [x] 使用 `npm create vue@latest` 创建项目
- [x] 选择 TypeScript + Router + Pinia + ESLint
- [x] 配置项目基础结构

#### 1.2 安装和配置依赖
- [x] 安装 Naive UI
- [x] 安装 Axios
- [x] 安装 Uno-CSS 及相关预设
- [x] 安装 dayjs（日期处理）
- [x] 配置 Uno-CSS（presets, shortcuts）

#### 1.3 配置开发环境
- [x] 创建 `.env` 和 `.env.example`
- [x] 配置 TypeScript 路径别名（@/ 别名）
- [x] 配置 Vite 路径别名
- [x] 配置 ESLint 和 Prettier
- [x] 创建目录结构

**🎯 阶段目标**: 项目可正常启动，开发环境配置完成 ✅

---

### 阶段二：基础设施（类型和服务）

#### 2.1 TypeScript 类型定义
- [x] 定义核心数据模型（User, StoryNode, StoryBook 等）
- [x] 定义 API 响应类型（ApiResponse, PaginatedResponse）
- [x] 创建类型统一导出文件

#### 2.2 API 服务层搭建
- [x] 配置 Axios 实例（baseURL, timeout）
- [x] 实现请求拦截器（添加 token）
- [x] 实现响应拦截器（401 处理、错误统一）
- [x] 创建各服务模块（对应后端 API 模块）
  - [x] auth.service.ts
  - [x] user.service.ts
  - [x] story.service.ts
  - [x] book.service.ts
  - [x] interaction.service.ts
  - [x] discovery.service.ts
  - [x] admin.service.ts
  - [x] upload.service.ts

**🎯 阶段目标**: 所有 API 调用有类型提示，服务层与后端对接完成 ✅

#### 2.3 状态管理（Pinia Stores）
- [x] 创建 auth store（登录、登出、用户信息）
- [x] 创建 user store（用户资料、统计）
- [x] 创建 story store（当前阅读的故事）
- [x] 创建 notification store（通知列表、未读数）
- [x] 创建 app store（全局状态：主题、侧边栏等）

**🎯 阶段目标**: 状态管理结构清晰，数据流向明确 ✅

#### 2.4 路由配置
- [x] 配置路由表（基础路由）
- [x] 实现路由守卫（权限检查、登录拦截）
- [x] 配置路由元信息（requiresAuth, requiresAdmin 等）
- [x] 实现路由懒加载

**🎯 阶段目标**: 路由跳转正常，权限控制生效 ✅

---

### 阶段三：公共组件（可复用组件）

#### 3.1 布局组件
- [ ] DefaultLayout.vue（顶部导航 + 主内容区 + 页脚）
- [ ] AuthLayout.vue（居中卡片式布局）
- [ ] AdminLayout.vue（侧边栏 + 主内容区）

#### 3.2 通用组件
- [ ] AppHeader.vue（导航、用户菜单、通知徽标）
- [ ] AppFooter.vue（页脚信息）
- [ ] LoadingSpinner.vue（加载动画）
- [ ] EmptyState.vue（空状态提示）

#### 3.3 表单组件
- [ ] LoginForm.vue
- [ ] RegisterForm.vue（含验证码发送）
- [ ] NodeEditor.vue（富文本编辑器）

**🎯 阶段目标**: 布局组件统一风格，通用组件可复用

---

### 阶段四：认证模块（登录注册）

#### 4.1 登录页面
- [ ] Login.vue（邮箱/密码登录）
- [ ] 表单验证
- [ ] 登录成功后跳转
- [ ] 错误提示

#### 4.2 注册流程
- [ ] Register.vue（邮箱、用户名、密码、验证码）
- [ ] 验证码发送（含倒计时）
- [ ] 邮箱验证功能
- [ ] 注册成功提示

#### 4.3 密码重置
- [ ] 忘记密码页面（发送验证码）
- [ ] 验证码验证
- [ ] 重置密码表单

**🎯 阶段目标**: 用户可以注册、登录、找回密码

---

### 阶段五：发现模块（Feed 和搜索）

#### 5.1 Feed 流
- [ ] Feed.vue（最新节点列表）
- [ ] 无限滚动/加载更多
- [ ] 节点卡片展示

#### 5.2 热门榜
- [ ] Trending.vue（按点赞数排序）
- [ ] 时间范围筛选（今日/本周/全部）

#### 5.3 搜索功能
- [ ] Search.vue（搜索框 + 结果列表）
- [ ] 防抖处理
- [ ] 关键词高亮

**🎯 阶段目标**: 用户可以浏览最新内容、查看热门、搜索内容

---

### 阶段六：活动模块（故事书）

#### 6.1 活动列表
- [ ] BookList.vue（卡片式展示）
- [ ] 活动信息（标题、描述、封面）
- [ ] 状态标识（进行中/已结束）

#### 6.2 活动详情
- [ ] BookDetail.vue（活动完整信息）
- [ ] 故事树概览
- [ ] 参与按钮
- [ ] 统计数据（节点数、参与人数）

**🎯 阶段目标**: 用户可以查看和参与活动

---

### 阶段七：故事模块（核心功能）

#### 7.1 故事树展示
- [ ] StoryTree.vue（树形结构可视化）
- [ ] 节点层级展示
- [ ] 折叠/展开功能

#### 7.2 阅读体验
- [ ] StoryRead.vue（阅读页面）
- [ ] 阅读路径展示（从根到当前节点）
- [ ] 分支选择器
- [ ] 节点详情展示

#### 7.3 续写功能
- [ ] StoryWrite.vue（续写页面）
- [ ] 父节点选择
- [ ] 内容编辑
- [ ] 提交审核

#### 7.4 节点管理
- [ ] 节点编辑（作者）
- [ ] 节点删除（叶子节点）
- [ ] 状态展示（审核中/已发布）

#### 7.5 互动功能
- [ ] 点赞/取消点赞
- [ ] 评论列表
- [ ] 发表评论
- [ ] 通知展示

**🎯 阶段目标**: 完整的阅读和续写体验，互动功能齐全

---

### 阶段八：用户模块（个人中心）

#### 8.1 用户主页
- [ ] Profile.vue（用户信息展示）
- [ ] 作品列表
- [ ] 个人资料编辑

#### 8.2 用户设置
- [ ] Settings.vue（账号设置）
- [ ] 头像上传
- [ ] 修改密码

#### 8.3 通知中心
- [ ] NotificationList.vue（通知列表）
- [ ] 未读/已读状态
- [ ] 标记已读
- [ ] 通知类型区分

**🎯 阶段目标**: 用户可以管理个人资料、查看通知

---

### 阶段九：管理模块（后台管理）

#### 9.1 管理员仪表盘
- [ ] Dashboard.vue（数据概览）
- [ ] 统计图表

#### 9.2 内容审核
- [ ] Audit.vue（待审核节点列表）
- [ ] 审核操作（通过/驳回）
- [ ] 审核历史

#### 9.3 用户管理
- [ ] UserManage.vue（用户列表）
- [ ] 封禁/解封
- [ ] 角色调整

**🎯 阶段目标**: 管理员可以审核内容、管理用户

---

### 阶段十：样式和优化

#### 10.1 Uno-CSS 样式
- [ ] 配置全局样式（colors, spacing）
- [ ] 创建组件样式
- [ ] 响应式设计（移动端适配）

#### 10.2 性能优化
- [ ] 路由懒加载
- [ ] 组件懒加载
- [ ] 图片懒加载
- [ ] 防抖/节流优化

#### 10.3 用户体验
- [ ] 加载状态
- [ ] 错误提示
- [ ] 空状态
- [ ] 过渡动画

**🎯 阶段目标**: 界面美观、性能优良、体验流畅

---

## 🔄 开发流程建议

### 开发顺序
1. **基础设施**（阶段一、二）→ 所有模块依赖
2. **认证模块**（阶段四）→ 其他模块需要登录
3. **公共组件**（阶段三）→ 其他页面复用
4. **发现 + 活动**（阶段五、六）→ 基础浏览功能
5. **故事模块**（阶段七）→ 核心功能
6. **用户 + 通知**（阶段八）→ 完整体验
7. **管理模块**（阶段九）→ 后台功能
8. **样式优化**（阶段十）→ 贯穿全程

### 开发原则
- **先服务层，后视图层**: API 接口对齐
- **先类型，后实现**: TypeScript 类型安全
- **先布局，后细节**: 整体框架优先
- **先功能，后样式**: 功能实现优先
- **先测试，后优化**: 基础功能验证

### 测试建议
- 每完成一个阶段，测试相关功能
- 使用后端 Swagger UI 测试 API
- 检查 TypeScript 类型错误
- 测试移动端响应式

### 协作建议
- **模块独立开发**: 按阶段分配任务
- **接口对齐**: 提前与后端确认 API
- **组件复用**: 公共组件优先开发
- **代码规范**: 统一代码风格

---

## 📌 技术要点提醒

### TypeScript
- 所有组件使用 `<script setup lang="ts">`
- 为所有 props 和 emits 定义类型
- 使用 interface 定义数据结构

### Pinia
- 使用 `defineStore` 创建 store
- 使用 `ref` 和 `computed` 管理状态
- 在组件中使用 `useXxxStore()` 访问

### Vue Router
- 路由懒加载：`() => import('...')`
- 路由守卫处理权限
- 使用 `router.push()` 导航

### Naive UI
- 按需导入组件
- 使用 NButton, NForm, NTable 等常用组件
- 自定义主题（可选）

### Uno-CSS
- 使用预设类（flex, grid, text-等）
- 自定义 shortcuts（如 flex-center）
- 避免写 CSS 文件，尽量用原子类

### Axios
- 统一错误处理
- Token 自动添加
- 响应拦截处理 401

---

## ✅ 检查点

每个阶段完成后，确保：
- [ ] 功能正常运行
- [ ] TypeScript 无错误
- [ ] 浏览器控制台无警告
- [ ] 响应式布局正常
- [ ] 与后端 API 对接成功

---

## 📚 参考资料

- [Vue 3 官方文档](https://vuejs.org/)
- [Pinia 官方文档](https://pinia.vuejs.org/)
- [Naive UI 官方文档](https://www.naiveui.com/)
- [Uno-CSS 官方文档](https://unocss.dev/)
- [Vue Router 官方文档](https://router.vuejs.org/)

---

**文档版本**: 1.0  
**更新日期**: 2026-02-06