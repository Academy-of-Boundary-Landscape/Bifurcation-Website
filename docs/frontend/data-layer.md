# 前端数据层统一约定

## 目标

前端现在不再把 API 调用、query key、缓存失效和页面逻辑混在一起写。

统一方向是：

- `services/http.ts`
  - 只负责 HTTP 基础能力、token 注入和通用请求函数
- `features/*/api.ts`
  - 负责资源级接口路径
- `features/*/queries.ts`
  - 负责 query key、查询和 mutation 的缓存策略
- `features/queryKeys.ts`
  - 负责共享 query key 定义
- `pages/*` / `components/*`
  - 优先消费 feature 层能力，不再重复发明一套接口协议

## 当前统一模式

### 1. 请求基础层

文件：

- `frontend/src/services/http.ts`

规则：

- `baseURL` 统一由 `http.ts` 提供，业务层不再手动拼 `/api/v1`
- token 注入统一由 axios request interceptor 处理
- 401 统一触发本地登出

### 2. 资源 API 层

文件：

- `frontend/src/features/admin/api.ts`
- `frontend/src/features/admin/queries.ts`
- `frontend/src/features/discovery/api.ts`
- `frontend/src/features/discovery/queries.ts`
- `frontend/src/features/story/api.ts`
- `frontend/src/features/interaction/api.ts`

规则：

- 同一类资源只保留一套正式路径
- 页面和组件如果还需要直接请求，优先先补到 feature API，再复用

当前已经明确的正式协议包括：

- 管理员仪表盘：`GET /admin/stats`
- 管理员用户列表：`GET /admin/users`
- 管理员更新用户：`PATCH /admin/users/{userId}`
- 管理员节点管理：`GET /admin/nodes`
- 待审核节点：`GET /admin/nodes/pending`
- 审核节点：`PATCH /admin/nodes/{nodeId}/audit`
- 节点详情：`GET /story/node/{nodeId}`
- 节点路径：`GET /story/node/{nodeId}/path`
- 分支阅读：`GET /story/node/{nodeId}/lineage`
- 评论列表：`GET /interaction/node/{nodeId}/comments`
- 创建评论：`POST /interaction/node/{nodeId}/comment`
- 删除评论：`DELETE /interaction/comment/{commentId}`
- 点赞：`POST /interaction/node/{nodeId}/like`
- 通知列表：`GET /interaction/notifications`
- 标记单条通知已读：`PUT /interaction/notifications/{notificationId}/read`
- 标记全部通知已读：`PUT /interaction/notifications/read`
- 最新动态：`GET /discovery/feed`
- 精选节点：`GET /discovery/featured`
- 热门节点：`GET /discovery/trending`
- 节点搜索：`GET /discovery/search`

### 3. Query Key 层

文件：

- `frontend/src/features/queryKeys.ts`

规则：

- 不再在各个页面里散写字符串 key
- 同一资源只能对应一套 key 名称
- 路由参数驱动的 key，在页面层应通过 `computed(() => queryKeys.xxx(...))` 传给 `useQuery`

当前统一 key：

- `books(params?)`
- `book(bookId)`
- `featuredNodes(params?)`
- `latestFeed(params?)`
- `trendingNodes(params?)`
- `discoverySearch(keyword, params?)`
- `storyTree(bookId)`
- `storyNode(nodeId)`
- `storyLineage(nodeId)`
- `nodePath(nodeId)`
- `nodeChildren(nodeId)`
- `nodeComments(nodeId, params?)`
- `pendingNodes(params?)`
- `adminNodes(params?)`
- `adminStats()`
- `adminUsers(params?)`
- `notifications(params?)`
- `unreadCount()`

### 4. 页面职责

页面现在应该优先负责：

- 读取路由参数
- 组合 query / mutation
- 管理界面状态
- 把状态传给展示组件

页面不应该继续负责：

- 手写一套与 feature 层重复的接口路径
- 自创另一套 query key 命名
- 直接改写 `useQuery` 返回数据作为长期状态管理方案

## 现在已经收口到统一模式的部分

### 故事树主链路

已对齐页面：

- `frontend/src/pages/books/BookDetailPage.vue`
- `frontend/src/pages/books/BookListPage.vue`
- `frontend/src/pages/story/StoryNodePage.vue`
- `frontend/src/pages/story/StoryLineagePage.vue`
- `frontend/src/pages/story/StoryWritePage.vue`

已对齐点：

- 节点详情、路径、子分支、完整分支阅读都已有对应的 feature query hook
- 故事册列表、单册详情、树数据和创作提交都已通过 `features/story/queries.ts` 暴露
- 节点详情相关 key 统一使用 `storyNode(nodeId)`
- 评论删除统一到 `DELETE /interaction/comment/{commentId}`
- 节点页评论更新改为 `invalidateQueries` 驱动
- 节点删除已回收到 `useDeleteStoryNodeMutation()`
- 书页和节点页对“是否允许继续创作”的判断统一复用 `features/story/creation.ts`

### 首页发现区

已对齐页面：

- `frontend/src/pages/home/HomePage.vue`

已对齐点：

- 首页“最新更新”改为复用 `features/discovery/queries.ts` 的 `useLatestFeedQuery()`
- 首页“精选节点”改为复用 `useFeaturedNodesQuery()`
- 首页“热门节点”改为复用 `useTrendingNodesQuery()`
- 首页节点搜索改为复用 `useDiscoverySearchQuery()`
- 发现能力也进入了共享 query key 体系，不再绕开前端统一数据层

### 通知与评论组件

已对齐组件：

- `frontend/src/components/interaction/CommentForm.vue`
- `frontend/src/components/interaction/CommentList.vue`
- `frontend/src/components/interaction/NotificationBell.vue`
- `frontend/src/components/interaction/NotificationPanel.vue`

已对齐点：

- 评论 API/query/mutation 现在只保留在 `features/interaction/*`
- 点赞按钮和通知铃铛都已改为复用 `features/interaction/queries.ts`
- 评论组件不再使用旧删评协议
- 通知页和通知面板统一复用 `features/interaction/queries.ts`
- `notifications` / `unread-count` key 改为共享定义
- 单条通知已读和全部已读都有正式 mutation hook

### 后台管理页面

已对齐页面：

- `frontend/src/pages/admin/AdminDashboardPage.vue`
- `frontend/src/pages/admin/AdminPendingNodesPage.vue`
- `frontend/src/pages/admin/AdminBooksPage.vue`
- `frontend/src/pages/admin/AdminUsersPage.vue`

已对齐点：

- 仪表盘改为复用 `GET /admin/stats`，不再调用前端臆造的统计接口
- 节点管理页改为复用 `features/admin/queries.ts` 中的 `useAdminNodesQuery()` 与 `useAuditStoryNodeMutation()`，并通过 `/admin/nodes` 统一查看全部节点、归档节点和待审核节点
- 故事册管理改为复用 `useBooksQuery()` 与 `useUpdateBookMutation()`
- 用户管理改为复用 `features/admin/queries.ts`

## 一致性检查结果

本轮检查重点关注了三类问题：

### 1. query key 是否混用

已修复：

- `story-node` 与 `node-detail` 并存的问题

当前结论：

- 关键故事节点链路已统一到 `storyNode(nodeId)`

### 2. 同一业务是否存在多套接口协议

已修复：

- 评论删除曾同时存在三种写法，现在统一到后端正式接口 `DELETE /interaction/comment/{commentId}`
- 评论 query/mutation 原先同时存在于 `story` 与 `interaction`，现在只保留在 `features/interaction/*`
- admin 审核能力原先混在 `story`，现在收回 `features/admin/*`

### 3. 页面是否继续散写请求

本轮结果：

- `pages/*` 与 `components/*` 中已经清掉了对 `get/post/put/del` 的直接业务调用
- 页面层现在主要负责组合 feature query / mutation 与界面状态

剩余注意点：

- `services/http.ts` 仍然是 feature API 的唯一请求入口
- 如果后续新增页面请求，应优先先补 `features/*/api.ts` 与 `features/*/queries.ts`
- 当前明显剩余的页面级直写数据入口主要是 `frontend/src/pages/user/ProfilePage.vue`

### 4. 缓存失效是否过宽

已继续收紧：

- `useBookQuery` 不再走“全量列表 + find”，改为正式单本接口
- 点赞 mutation 现在支持按 `bookId` 精确失效当前故事树；没有 `bookId` 时才退回到故事树前缀失效
- 删评 mutation 改为必须带 `nodeId`，只刷新当前节点评论与节点详情
- 全部通知已读改为通过 `notificationsRoot()` 和 `unreadCount()` 统一失效

当前结论：

- 关键故事节点、评论、通知和后台链路的缓存失效已经比前一轮更精确
- 页面级直写请求已经清掉，后续重点转向避免 feature 层重复能力

## 后续收口建议

按优先级建议继续做：

1. 继续把后台页也拉到同样的数据层模式，避免 admin 页面重新长出页面直写请求
2. 视情况收掉 `features/story/queries.ts` 与 `features/interaction/queries.ts` 的重复能力，避免 story/interaction 两侧都维护评论相关 hook
3. 如果后续要引入分页或无限滚动，优先扩展共享 query key 和 feature query，而不是在页面里另起一套状态管理

## 结论

前端现在已经不再是“每个页面自己定义一套接口与缓存规则”的状态，核心阅读、评论、通知链路已经基本收口到统一数据层。

当前最重要的共识是：

- key 名称统一由 `features/queryKeys.ts` 提供
- 正式协议统一由 `features/*/api.ts` 提供
- 查询与 mutation 优先由 `features/*/queries.ts` 暴露
- feature 职责按领域划分：`story` 负责故事资源，`interaction` 负责互动资源，`admin` 负责后台资源
- 页面层优先组合，不再重复定义资源协议
