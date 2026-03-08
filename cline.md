# “分岔视界（Bifurcation Horizon）”前端架构与开发指导文档

> 面向：前端开发者 / 协作同伴 / Cline / Claude Code
> 技术栈：**Vue 3 + TypeScript + Vite + Naive UI + UnoCSS + Vue Router + Pinia**
> 后端：**FastAPI**
> 文档目标：为“树状图结构小说续写网站”提供一份可执行、可维护、可持续扩展的前端设计与开发规范。

---
# 0. 基本信息

前端请在/root/bifurcation-prj/frontend 文件夹里面进行开发
后端在/root/bifurcation-prj/backend/文件夹里面

后端的文档集中在/backend/developer_guide.md（总览）和worklist.md（细节）里面

如果你在前端做完了一些阶段性改动，我希望你把改动开一个文档进行记录，方便你后续开发。

# 1. 项目目标与设计原则

## 1.1 产品目标

这是一个以“树状叙事”为核心的线上续写平台。用户围绕若干故事起点，不断在已有节点上进行：

* 线性续写
* 新分支开辟
* 节点评论互动
* 点赞反馈
* 审核发布
* 后期静态展示

前端的职责，不只是“把 API 接起来”，而是要把这种**分叉叙事的阅读感、探索感、世界线感**做出来。

这个网站的前端体验必须回答三个核心问题：

1. **用户如何快速理解一棵故事树？**
2. **用户如何顺畅地阅读一条分支，并决定从哪里继续写？**
3. **用户如何在复杂树结构中不迷路？**

---

## 1.2 前端总原则

前端设计遵循以下原则：

### A. 结构优先于花哨

树状叙事本身已经复杂，前端不能再用过度装饰干扰信息理解。布局、导航、层级、状态反馈必须清楚。

### B. 阅读体验优先于后台管理体验

本项目是“故事网站”，不是传统管理后台。游客和作者看到的内容应该更接近“小说阅读器 + 分支地图”，而不是 CRUD 面板。

### C. 组件必须高复用

树节点卡片、评论区、时间线、分支导航、创作编辑器、审核面板等都必须模块化，避免后续改动牵一发动全身。

### D. 风格统一、克制、未来感

视觉风格建议：

* **黑白主色**
* **高对比、低饱和**
* **大面积留白 / 留黑**
* **细线框、几何边角、轻微发光感**
* **少量动效，强调“界面扫描 / 世界线切换 / 节点激活”**

关键词：

* 极简
* 冷感
* 科幻终端
* 档案馆
* 世界线观测界面

### E. 先把主链路做通，再做炫技

优先级必须是：

1. 基础路由和页面骨架
2. 认证与权限
3. 书籍列表页
4. 故事树浏览页
5. 节点详情页
6. 创作页（续写 / 创建分支）
7. 评论、点赞、通知
8. 管理审核
9. 搜索、排行榜、AI 摘要、动态动效

---

# 2. 推荐前端工程方案

## 2.1 技术选型建议

推荐前端基础栈如下：

* **Vue 3**：核心框架
* **TypeScript**：强制使用
* **Vite**：构建工具
* **Vue Router**：路由管理
* **Pinia**：全局状态管理
* **Naive UI**：基础组件
* **UnoCSS**：原子化样式
* **@vueuse/core**：工具函数
* **Markdown 渲染库**（可选）：如果节点内容后续支持 markdown
* **Vue Query / TanStack Query for Vue**（强烈建议） ：服务端状态管理、请求缓存、失效刷新

> 建议：不要把所有异步请求都塞进 Pinia。
> 用户状态、UI 状态进 Pinia；服务端数据优先用 Query 管。

---

## 2.2 推荐目录结构

```txt
src/
├── app/
│   ├── App.vue
│   ├── main.ts
│   ├── router/
│   │   ├── index.ts
│   │   └── guards.ts
│   └── providers/
│       └── naive-provider.vue
│
├── assets/
│   ├── styles/
│   │   ├── reset.css
│   │   ├── theme.css
│   │   ├── transitions.css
│   │   └── tokens.css
│   └── icons/
│
├── components/
│   ├── common/
│   │   ├── AppHeader.vue
│   │   ├── AppFooter.vue
│   │   ├── AppLogo.vue
│   │   ├── EmptyState.vue
│   │   ├── LoadingBlock.vue
│   │   ├── ErrorBlock.vue
│   │   ├── PageTitle.vue
│   │   ├── UserAvatar.vue
│   │   └── ConfirmDialog.vue
│   │
│   ├── story/
│   │   ├── StoryBookCard.vue
│   │   ├── StoryTreePanel.vue
│   │   ├── StoryTreeNode.vue
│   │   ├── StoryBranchPath.vue
│   │   ├── StoryNodeCard.vue
│   │   ├── StoryNodeMeta.vue
│   │   ├── StoryNodeActions.vue
│   │   ├── StoryReader.vue
│   │   ├── StoryBranchMiniMap.vue
│   │   ├── StoryCreateEntry.vue
│   │   └── StoryStatusBadge.vue
│   │
│   ├── editor/
│   │   ├── NodeEditor.vue
│   │   ├── NodeEditorToolbar.vue
│   │   ├── NodePreview.vue
│   │   ├── BranchTypeSelector.vue
│   │   └── DraftGuard.vue
│   │
│   ├── interaction/
│   │   ├── LikeButton.vue
│   │   ├── CommentList.vue
│   │   ├── CommentForm.vue
│   │   ├── NotificationBell.vue
│   │   ├── NotificationPanel.vue
│   │   └── ShareActions.vue
│   │
│   ├── auth/
│   │   ├── LoginForm.vue
│   │   ├── RegisterForm.vue
│   │   ├── EmailCodeInput.vue
│   │   └── AuthGuardNotice.vue
│   │
│   └── admin/
│       ├── PendingNodeList.vue
│       ├── AuditActionBar.vue
│       ├── AuditReasonDialog.vue
│       ├── BookPhaseManager.vue
│       └── AdminStatsPanel.vue
│
├── composables/
│   ├── useAuth.ts
│   ├── useTheme.ts
│   ├── useStoryTree.ts
│   ├── useStoryReader.ts
│   ├── useNodeActions.ts
│   ├── useNotifications.ts
│   ├── usePagination.ts
│   └── usePageTitle.ts
│
├── features/
│   ├── auth/
│   │   ├── api.ts
│   │   ├── queries.ts
│   │   ├── store.ts
│   │   └── types.ts
│   │
│   ├── story/
│   │   ├── api.ts
│   │   ├── queries.ts
│   │   ├── adapters.ts
│   │   ├── types.ts
│   │   └── utils.ts
│   │
│   ├── interaction/
│   │   ├── api.ts
│   │   ├── queries.ts
│   │   ├── types.ts
│   │   └── utils.ts
│   │
│   └── admin/
│       ├── api.ts
│       ├── queries.ts
│       ├── types.ts
│       └── utils.ts
│
├── layouts/
│   ├── PublicLayout.vue
│   ├── AuthLayout.vue
│   ├── DashboardLayout.vue
│   └── AdminLayout.vue
│
├── pages/
│   ├── home/
│   │   └── HomePage.vue
│   ├── books/
│   │   ├── BookListPage.vue
│   │   └── BookDetailPage.vue
│   ├── story/
│   │   ├── StoryNodePage.vue
│   │   ├── StoryWritePage.vue
│   │   └── StoryLineagePage.vue
│   ├── auth/
│   │   ├── LoginPage.vue
│   │   ├── RegisterPage.vue
│   │   └── ProfilePage.vue
│   ├── notifications/
│   │   └── NotificationPage.vue
│   ├── admin/
│   │   ├── AdminDashboardPage.vue
│   │   ├── AdminPendingNodesPage.vue
│   │   └── AdminBooksPage.vue
│   └── misc/
│       ├── NotFoundPage.vue
│       └── ForbiddenPage.vue
│
├── services/
│   ├── http.ts
│   ├── auth-token.ts
│   ├── query-client.ts
│   └── error-handler.ts
│
├── stores/
│   ├── ui.ts
│   ├── auth.ts
│   └── draft.ts
│
├── types/
│   ├── api.ts
│   ├── common.ts
│   └── ui.ts
│
└── utils/
    ├── date.ts
    ├── tree.ts
    ├── text.ts
    ├── route.ts
    └── guards.ts
```

---

# 3. 信息架构与页面设计

这部分是整个前端最核心的内容。

---

## 3.1 页面总览

建议最少包含以下页面：

### 公共页面

1. **首页 HomePage**
2. **故事册列表页 BookListPage**
3. **故事册详情页 BookDetailPage**
4. **故事节点详情页 StoryNodePage**
5. **完整分支阅读页 StoryLineagePage**
6. **登录页 LoginPage**
7. **注册页 RegisterPage**
8. **个人中心 ProfilePage**
9. **通知页 NotificationPage**
10. **404 / 403 页面**

### 创作页面

11. **续写 / 新建分支页 StoryWritePage**

### 管理页面

12. **管理员总览页 AdminDashboardPage**
13. **待审核节点页 AdminPendingNodesPage**
14. **故事册管理页 AdminBooksPage**

---

## 3.2 核心导航结构

推荐顶栏导航：

* 首页
* 故事册
* 创作说明 / 活动规则
* 排行 / 热门（后期可加）
* 通知（登录后）
* 个人中心（登录后）
* 管理台（管理员可见）

推荐移动端或窄屏下折叠为菜单。

---

# 4. 关键页面详细设计

## 4.1 首页 HomePage

### 页面目标

首页不是普通 landing page，而是活动入口。它要在最短时间内让访客理解：

* 这是一个什么活动
* 为什么有意思
* 我应该点哪里开始读
* 我如何参与

### 页面结构建议

#### 区块 A：首屏 Hero

内容建议：

* 项目标题：分岔视界 / Bifurcation Horizon
* 一句副标题：

  * 例如：**沿着秘封组的故事继续前进，或亲手开启新的世界线。**
* 两个主按钮：

  * 开始阅读
  * 我要创作

视觉建议：

* 黑底白字
* 中央大标题
* 背景使用轻微网格、坐标线、扫描线、树状连接线抽象图
* 不要用复杂插画盖住信息

#### 区块 B：活动简介

用 3～4 个信息块说明：

* 树状叙事机制
* 续写 / 分支玩法
* 审核机制
* 最终展示 / 奖项

#### 区块 C：当前开放中的故事册

展示正在写作阶段的 story books 卡片。

字段：

* 封面
* 标题
* 简介
* 当前阶段
* 节点数 / 分支数（如果有）
* 进入阅读按钮

#### 区块 D：参与流程

用时间线或四步卡片表达：

* 注册登录
* 读前文
* 续写或开分支
* 等待审核发布

#### 区块 E：最新发布 / 热门节点（后期）

如果你后端有接口，可以加；没有就先不做。

---

## 4.2 故事册列表页 BookListPage

### 页面目标

给用户选择故事入口。

### 展示方式

推荐使用**卡片宫格 + 筛选器**。

### 筛选维度

* 按阶段：drafting / writing / showcase / archived
* 按更新时间（后期）
* 按热度（后期）

### 单卡片建议信息

* 标题
* 描述
* 阶段 badge
* 是否开放新节点
* 起止时间
* 进入按钮

### 交互要求

* 点击卡片进入 `BookDetailPage`
* 支持 skeleton loading
* 空状态友好

---

## 4.3 故事册详情页 BookDetailPage

### 页面目标

这是“树状叙事”的核心入口页。

用户在这里需要完成三件事：

1. 理解本故事册是什么
2. 看到整棵故事树的概貌
3. 进入某个节点或某条分支继续阅读

### 页面布局建议

推荐采用：**左树右详情** 或 **上方简介 + 下方树状区**。

桌面端建议：

* 左侧：故事树 / 节点关系图 / 分支目录
* 右侧：故事册简介、起始设定、根节点列表、说明操作

窄屏建议改为上下结构。

### 必备区块

#### A. 故事册头部信息

* 标题
* 描述
* 当前阶段
* 开放状态
* 时间信息
* 操作按钮：开始阅读 / 查看全部分支 / 我要续写（登录后）

#### B. 根节点列表

如果一个 book 有多个故事开头，这里需要明确列出来。

#### C. 树状展示区

这里非常关键。

推荐第一阶段先做 **“可折叠树列表 + 缩进结构”**，不要一开始就做复杂自由画布。

原因：

* 开发简单
* 可读性高
* 移动端兼容好
* 可维护性远高于自绘节点图

树节点每项显示：

* branch_name 或 title
* 作者
* 点赞数 / 评论数 / 子分支数
* 是否完结
* 发布时间
* 快速按钮：查看、沿此续写、创建分支

#### D. 分支导航说明

告诉用户：

* “续写”只能对未完结叶节点进行
* “创建分支”可以从任意节点发起
* “结局节点”不能再续写

---

## 4.4 节点详情页 StoryNodePage

### 页面目标

这是具体阅读与互动页面。

用户需要在这里：

* 阅读节点内容
* 看它处于哪条故事线上
* 看它有哪些子分支
* 点赞评论
* 决定是否从这里继续创作

### 页面建议结构

#### A. 路径导航区

显示该节点在线路中的位置，例如：

根节点 → 分支 A → 分支 A-2 → 当前节点

这部分非常重要，它是“防迷路装置”。

组件建议：`StoryBranchPath.vue`

#### B. 节点元信息区

* 节点标题 / 分支名
* 作者
* 发布时间
* 状态（待审核 / 已发布 / 已归档）
* 点赞 / 评论计数

#### C. 正文阅读区

* 大字号标题
* 舒适行高
* 阅读宽度控制在 680px～820px 左右
* 适当使用分段与空白

#### D. 节点操作区

* 点赞
* 评论
* 分享（后期）
* 沿此续写
* 从此处分叉

#### E. 子分支区

显示该节点的直接 children。

推荐展示成“分支列表卡片”，而不是一开始强做图可视化。

每个子分支显示：

* 分支名
* 作者
* 摘要
* 点赞
* 评论
* 进入分支按钮

#### F. 评论区

* 评论列表
* 发表评论
* 删除自己的评论

---

## 4.5 完整分支阅读页 StoryLineagePage

### 页面目标

这个页面是本项目体验上的亮点之一。

它不是只看一个节点，而是把“从根到当前节点的一整条线”串起来给人读。

这是非常必要的，因为用户在决定续写之前，往往需要重新阅读这一整条线路。

### 页面结构建议

* 顶部显示当前分支路径
* 主体按时间顺序纵向串联所有祖先节点 + 当前节点
* 每个节点用分段卡片或章节块展示
* 当前节点高亮
* 页面底部给出：

  * 沿当前节点继续写
  * 从某个祖先节点重新开分支

### 价值

这是整个“树状小说网站”最应该做好的阅读页之一。
建议优先级很高。

---

## 4.6 创作页 StoryWritePage

### 页面目标

用户从某个节点出发，进行：

* 直接续写
* 创建新分支

### 页面模式

建议该页用两种模式，但复用同一个编辑器页面：

* `mode=continue`
* `mode=branch`

### 页面结构

#### A. 前文摘要区

至少要显示：

* 当前挂载节点标题
* 所在线路路径
* 上一节点摘要 / 当前节点摘要
* 可选：展开查看全文

这样做是为了防止作者写串线。

#### B. 创作类型说明

如果是续写：

* 说明这是对当前叶节点的直接延伸

如果是分支：

* 说明这是从该节点分裂出来的新可能性
* 必须填写 branch_name

#### C. 编辑器主体

字段建议：

* title（可选，视规则）
* branch_name（分支模式下强提示）
* summary
* content
* zone（long / short）

#### D. 提交区

* 保存草稿（前端本地）
* 提交审核
* 离开提醒

### 编辑器建议

第一版不用追求富文本，**普通 textarea / markdown 文本框就够了**。

因为你的内容核心是纯文本小说，不是图文排版。

### 必须做的保护

* 本地草稿缓存
* 未保存离开提醒
* 提交前字数检查
* 提交中禁用按钮

---

## 4.7 登录 / 注册 / 个人中心

### 登录页

* 用户名 / 邮箱
* 密码
* 登录按钮
* 去注册入口

### 注册页

按你后端流程做成三段式或一步式引导：

1. 输入邮箱
2. 获取验证码
3. 验证邮箱
4. 填写用户名、密码并注册

### 个人中心 ProfilePage

建议包含：

* 基本资料
* 我的投稿节点
* 我的收到的点赞 / 评论统计
* 我的通知入口
* 账号状态（writer / admin / banned）

---

## 4.8 通知页 NotificationPage

### 页面目标

给创作者建立“反馈回路”。

通知类型：

* 有人从我的节点开了分支
* 有人点赞我的节点
* 有人评论我的节点
* 我的投稿通过审核
* 我的投稿被驳回

### 建议功能

* 按未读 / 全部筛选
* 一键全部标记已读
* 点击跳转到相关节点

---

## 4.9 管理后台 Admin

### 管理台首页 AdminDashboardPage

推荐内容：

* 待审核节点数量
* 今日新增节点
* 总节点数 / 用户数 / 评论数
* 快速跳转：待审核 / 故事册管理

### 待审核页 AdminPendingNodesPage

核心功能：

* 查看待审核节点列表
* 阅读正文
* 审核通过
* 驳回并填写理由

建议布局：

* 左侧列表
* 右侧详情审阅

### 故事册管理页 AdminBooksPage

第一版可只做最基础：

* 查看 book 列表
* 修改 phase
* 控制 allow_new_nodes

---

# 5. 路由设计建议

```ts
/
/books
/books/:bookId
/story/node/:nodeId
/story/lineage/:nodeId
/story/write/:bookId
/login
/register
/profile
/notifications
/admin
/admin/pending
/admin/books
/403
/:pathMatch(.*)*
```

建议 query 参数：

* `/story/write/:bookId?parentId=12&mode=continue`
* `/story/write/:bookId?parentId=12&mode=branch`
* `/books?phase=writing`

---

# 6. 状态管理设计

## 6.1 哪些东西进 Pinia

适合进入 Pinia：

### auth store

* accessToken
* currentUser
* isAuthenticated
* role

### ui store

* 全局 loading
* 侧边栏开关
* 主题模式（虽然你主要黑白，仍建议留接口）
* 弹窗状态（少量）

### draft store

* 本地草稿
* 草稿时间戳
* 草稿对应 parentId / bookId

---

## 6.2 哪些东西不要进 Pinia

以下更适合交给 Query：

* story books 列表
* story tree
* node detail
* comments
* notifications
* pending nodes

原因：

* 这些是典型服务端状态
* 有缓存、失效、重拉需求
* 不应该手写大量重复 loading/error/data 三件套

---

# 7. API 接入层设计规范

你已经有后端文档，所以前端需要再往前一步，建立“可维护的 API 层”。

## 7.1 不要在页面里直接 fetch

必须分层：

* `services/http.ts`：底层请求器
* `features/*/api.ts`：具体接口
* `features/*/queries.ts`：query hooks
* `pages/*`：只消费 hooks / composables

---

## 7.2 推荐 HTTP 封装结构

```ts
// services/http.ts
export async function http<T>(url: string, options?: RequestInit): Promise<T>
```

要求：

* 自动拼接 base url
* 自动附带 token
* 自动解析错误
* 统一抛出业务错误
* 兼容 form-data / x-www-form-urlencoded

---

## 7.3 示例：story 模块分层

```ts
// features/story/api.ts
export function fetchBooks(params?: { phase?: string }) {}
export function fetchBookTree(bookId: number) {}
export function fetchNodeDetail(nodeId: number) {}
export function createStoryNode(payload: CreateNodePayload) {}

// features/story/queries.ts
export function useBooksQuery(params?: { phase?: string }) {}
export function useBookTreeQuery(bookId: number) {}
export function useNodeDetailQuery(nodeId: number) {}
export function useCreateNodeMutation() {}
```

---

# 8. 组件设计原则

## 8.1 组件分层

建议把组件分成三层：

### 展示组件（Presentational）

只负责 UI，不直接请求数据。

例如：

* StoryNodeMeta
* StoryBookCard
* LikeButton
* EmptyState

### 容器组件（Container）

负责取数据、拼装 props。

例如：

* StoryTreePanel
* PendingNodeList

### 页面组件（Page）

负责路由参数、页面级逻辑、布局。

---

## 8.2 重要可复用组件清单

### StoryTreeNode

这是最重要的组件之一。

它应该支持：

* 展示节点基本信息
* 展示 children
* 折叠/展开
* 当前节点高亮
* 操作按钮插槽

### StoryNodeCard

用于节点详情页、分支列表、审核列表等多个场景。

### NodeEditor

创作页核心组件。

必须做到：

* 可控输入
* 支持草稿恢复
* 支持 preview（可选）
* 支持提交态

### CommentList / CommentForm

评论区应与业务解耦，可在节点页、管理页复用。

---

# 9. 树状叙事的前端表示策略

这是你项目最特殊的部分。

## 9.1 第一阶段不要做复杂自由拖拽树图

虽然“树图可视化”很酷，但第一阶段不建议：

* 自由布局图
* 拖拽画布
* 力导向图
* SVG 大型关系图

原因：

* 阅读体验未必最好
* 移动端差
* 可维护性差
* 复杂树很容易炸

## 9.2 第一阶段推荐做法：三层表现

### 表现 1：缩进树

用于 BookDetailPage 主视图。
最稳妥。

### 表现 2：路径面包屑

用于 NodePage / WritePage。
帮助用户定位。

### 表现 3：完整分支纵向阅读

用于 LineagePage。
提升阅读连续性。

这三种组合，已经足够支撑你的主玩法。

## 9.3 第二阶段再考虑高级可视化

后续可以增加：

* 迷你树图 minimap
* 横向世界线图
* 时间 / 深度切换视图
* 按热度高亮分支

---

# 10. UI / 视觉风格规范

## 10.1 总体风格关键词

* 黑白
* 终端感
* 观测站
* 档案库
* 科幻但克制
* 像“记录平行世界分支”的界面

---

## 10.2 色彩建议

主色不要复杂，建议：

* `#000000`：背景主黑
* `#0f0f0f`：容器底色
* `#ffffff`：主文字
* `#d9d9d9`：次级文字
* `#666666`：弱提示
* `#1f1f1f`：边框/分割
* `#fafafa`：浅色模式备用（如果以后要做）

强调色建议非常克制：

* 冷白发光
* 或极淡青灰

但不要大面积蓝紫霓虹，不然会变廉价“赛博朋克模板站”。

---

## 10.3 形状与边框

建议：

* 大量使用直线、细边框、矩形分区
* 小圆角或几乎不圆角
* 卡片边缘可做轻微切角感
* 分隔线清晰

---

## 10.4 动效建议

动效要轻：

* hover 时边框亮起
* 展开树节点时高度过渡
* 页面切换时淡入
* 通知红点轻微呼吸
* 当前节点高亮时有扫描线/描边移动感（可选）

不要做：

* 大片漂浮粒子
* 重 3D 特效
* 长时间炫技动画

---

## 10.5 字体建议

如果中文为主：

* 无衬线中文字体优先
* 标题可以稍微窄体、几何感
* 正文阅读要保证清晰和长文舒适性

正文区域千万不要过分未来字体，否则阅读疲劳。

---

# 11. UnoCSS 与 Naive UI 协作建议

## 11.1 原则

* **Naive UI 负责基础组件和交互稳定性**
* **UnoCSS 负责布局、间距、风格细化**

不要反过来。

## 11.2 建议

### 适合 Naive UI 的部分

* Button
* Input
* Form
* Dialog
* Dropdown
* Tabs
* Drawer
* Message / Notification
* Skeleton

### 适合 UnoCSS 的部分

* 页面布局
* 容器宽度
* 网格
* 边框
* 间距
* 字体大小
* 自定义 hover / transition

---

# 12. 可维护性规范

## 12.1 TypeScript 严格模式

必须开启严格模式，不要偷懒用 `any`。

## 12.2 API 类型与 UI 类型分离

后端返回的数据类型，不应直接污染 UI。

建议：

* `features/story/types.ts` 放 API types
* `features/story/adapters.ts` 做字段适配
* 页面使用更稳定的 view model

## 12.3 不要把业务逻辑写进模板

模板只做展示；复杂判断放进：

* computed
* composables
* utils

## 12.4 统一空态 / 错误态 / loading 态

所有主要页面都应该统一处理：

* loading skeleton
* empty state
* error state

不要让每页各写一套。

## 12.5 命名规范

* 组件：PascalCase
* composable：`useXxx`
* query key：统一常量化
* 页面组件结尾统一 `Page`

---

# 13. 建议的开发优先级

下面是我建议前端实际开发顺序。

## P0：基础设施

1. 初始化项目脚手架
2. 接入 Naive UI + UnoCSS + Router + Pinia
3. 建立 http 请求封装
4. 建立 auth store
5. 建立全局布局、Header、Footer、错误页
6. 建立主题 token 与基础样式系统

## P1：主链路阅读功能

7. 首页
8. 故事册列表页
9. 故事册详情页
10. 树状节点展示组件
11. 节点详情页
12. 完整分支阅读页

## P2：创作功能

13. 登录页
14. 注册页
15. 创作页（续写 / 分支）
16. 本地草稿保护
17. 提交审核流程

## P3：互动功能

18. 点赞
19. 评论
20. 通知系统
21. 个人中心

## P4：管理员功能

22. 管理台首页
23. 待审核列表
24. 审核详情与通过/驳回
25. 故事册状态管理

## P5：增强与美化

26. 搜索 / 热门 / 榜单
27. 分支 minimap
28. 动效增强
29. AI 摘要（如果后端支持）
30. SEO / 静态展示优化

---

# 14. 给 Cline / Claude Code 的落地执行要求

下面这段可以直接视为对代码代理的开发约束。

## 14.1 代码生成原则

1. 所有新代码必须使用 TypeScript。
2. 所有页面均采用 Vue 3 `<script setup lang="ts">`。
3. 所有样式优先使用 UnoCSS 原子类，复杂公共样式放到主题文件。
4. 所有基础交互组件优先使用 Naive UI。
5. 严禁在页面组件里直接写裸 fetch。
6. API 请求必须经过 `services/http.ts` 与 feature `api.ts`。
7. 所有服务端数据必须提供 loading / empty / error 三态处理。
8. 所有路由页面必须设置页面标题。
9. 所有关键表单必须有校验与提交中状态。
10. 所有需要登录的页面或操作必须接入路由守卫或操作守卫。

## 14.2 组件开发要求

* 单个组件尽量职责单一。
* 单文件组件超过 250～300 行时，优先拆分。
* 树节点展示逻辑必须抽离成独立组件，不得散落到多个页面。
* 编辑器必须是独立组件，不得直接写死在页面里。

## 14.3 页面实现要求

* 先实现桌面端，再兼容移动端。
* 但从第一版起，就必须保证窄屏不炸布局。
* 页面主体宽度应统一，不要每页都不同。

---

# 15. 第一版 MVP 的最小交付范围

如果你现在资源有限，我建议第一版只做下面这些：

## 必做

* 首页
* 故事册列表页
* 故事册详情页
* 缩进树展示
* 节点详情页
* 完整分支阅读页
* 登录 / 注册
* 创作页
* 评论
* 点赞
* 通知页
* 待审核页

## 可以暂缓

* 高级树图可视化
* 搜索
* 热门榜单
* AI 总结
* 分享海报
* 富文本编辑器
* 深色 / 浅色双主题切换

---

# 16. 我对这个项目的最终架构建议

如果只给一句总建议，那就是：

**不要把它做成“普通 CMS 网站 + 树形数据展示”，而要把它做成“分支阅读器 + 创作入口 + 审核社区”的三位一体产品。**

在前端上，真正最值钱的部分不是表单，不是管理页，而是以下三件事：

1. **故事树怎么被理解**
2. **分支路径怎么被阅读**
3. **用户从阅读切换到创作时是否顺畅**

只要这三点做好，这个网站就会显得很有“技术味”和“产品感”；反之，就会退化成一个普通投稿站。

---

# 17. 后续建议

建议你下一步继续做两份东西：

1. **前端 worklist / 任务拆解表**：把上述页面和组件拆成具体 issue
2. **设计稿草图文档**：哪怕只是线框图，也能极大减少前端返工

如果要继续，我建议下一步直接输出：

* 一份“前端开发任务清单（按优先级拆分到 issue 级别）”
* 或者一份“Vue 项目目录初始化模板 + 路由骨架 + store 骨架”
