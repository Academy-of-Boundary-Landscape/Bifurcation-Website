# 前端数据需求与「指标说谎」审计

> 审计对象：`frontend/src`（Vue 3 + TS + TanStack Query）
> 目的：逐页梳理每个用户可见的数字指标，标记哪些是**真实总数**、哪些在**说谎**（把被 limit 截断的数组长度当成站点/全局总数）、哪些**缺失**（前端想要总数但后端没有，于是省略或退化）。
> 约定：后端 list 接口返回裸 `List[...]`，带 skip/limit，**不带 total count**。凡是「数组长度被当成总数」即判定为说谎。

---

## 概览

- 整体上**详情类指标比较诚实**：节点详情页、故事树检视器、书详情页用的都是 denormalized 字段（`node.likes_count` / `comments_count` / `children_count`）或**完整无 limit 的故事树**，这些是真实总数。
- **说谎集中在「列表长度被当成总数」的场景**，主要有四类：
  1. 首页 hero 的三个 telemetry（受 `limit:4` 截断）—— 已在注释里自认是 `SHOWN`（已显示数），属于「半诚实」，但仍是被截断的数组长度。
  2. **个人中心 hero 的「Nodes」**＝ `submittedNodes?.length`（`limit:5`），但 `User` 类型上已有真实字段 `nodes_count`，属于明确说谎且有现成替代字段。
  3. **管理端列表统计**：待审核页 hero 三卡（`limit:80` 数组的 filter 长度）、用户管理 hero（`limit` 数组长度）。注意管理端 Dashboard 用 `/admin/stats` 是真实的。
  4. **节点详情页「子分支（N）」标题**＝ `children.length`（`limit:5`），而同一页面 `node.children_count` 是真实总数却没被用在这个标题上。
- 真正缺失的后端能力：**list 接口的总数（X-Total-Count 或 `{items,total}` 包络）**，以及**站点级聚合数**（featured/latest/trending 全量计数、通知总数）。

---

## 按页面分组

### 1. 首页 HomePage
**文件**：`frontend/src/pages/home/HomePage.vue`

**消费的接口 / hooks**
- `useFeaturedNodesQuery({ limit: 4 })` → `GET /discovery/featured`（L98）
- `useLatestFeedQuery({ limit: 4 })` → `GET /discovery/feed`（L99）
- `useTrendingNodesQuery({ days: 7, limit: 4 })` → `GET /discovery/trending`（L100）
- `useDiscoverySearchQuery(keyword, { limit: 6 })` → `GET /discovery/search`（L101-105）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「SHOWN · 编辑标记」 | `featuredNodes.value?.length`（limit:4） | **说谎**（半诚实，标了 SHOWN，但仍是被截断数组长度，不是站点 featured 总数） | 定义 L113，渲染 L305 |
| Hero「SHOWN · 近期入档」 | `latestFeed.value?.length`（limit:4） | **说谎**（同上） | 定义 L112，渲染 L309 |
| Hero「SHOWN · 高度关注」 | `trendingNodes.value?.length`（limit:4） | **说谎**（同上） | 定义 L114，渲染 L311 |
| 卡片内 LIKES / CHILDREN / COMMENTS | `node.likes_count` / `children_count` / `comments_count` | **真实**（denormalized 字段） | L189-190, L212-213, L229 |
| 搜索「MATCHED N ENTRIES」 | `searchResults.length`（limit:6） | **说谎**（命中数被 limit 截断；用户会以为只匹配到 N 条，实际可能更多） | L525 |

> 说明：作者在 L297-298 注释里坦白了 hero 三个数是 `query.length` 受 limit 截断，需要后端 count 接口。搜索的 MATCHED 没有这层自觉。

---

### 2. 个人中心 ProfilePage
**文件**：`frontend/src/pages/user/ProfilePage.vue`

**消费的接口 / hooks**
- `useMyProfileQuery()` → `GET /auth/me`（L16，返回 `User`，含 `nodes_count?` / `likes_count?`）
- `useUserNodesQuery({ authorId, limit: 5 })` → `GET /story/user/{id}/nodes`（L18-22）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「Role」 | `user?.role` | **真实** | L168 |
| Hero「Nodes」 | `submittedNodes?.length \|\| 0`（limit:5，**最多显示 5**） | **说谎**（应使用 `user.nodes_count`，该真实字段已在 `User` 类型上，见 `types/models.ts:19`） | L172 |
| 「最近提交的 N 个节点」文案 | `submittedNodes?.length`（limit:5） | **说谎**（措辞「最近 N 个」勉强自洽，但和 hero 同源、同样被截断） | L300 |
| 节点卡片 `N 赞 / N 评论 / N 分支` | `node.likes_count` / `comments_count` / `children_count` | **真实** | L334-336 |
| 邮箱 / 注册时间 / 角色 | `user.email` / `created_at` / `role` | **真实** | L248-278 |

> 这是「有现成真实字段却仍用截断长度」的典型案例：`User.nodes_count` 已存在，但 hero 用了 `submittedNodes.length`。

---

### 3. 管理端 · 仪表盘 AdminDashboardPage
**文件**：`frontend/src/pages/admin/AdminDashboardPage.vue`

**消费的接口 / hooks**
- `useAdminStatsQuery()` → `GET /admin/stats`（返回 `AdminDashboardStats`，含 users/nodes 各项 total）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「N 个待审核节点」 | `stats.nodes.pending` | **真实** | L79-81 |
| Hero「N 位新用户 / N 个新节点（近7日）」 | `stats.users.new_7d` / `stats.nodes.new_7d` | **真实** | L82 |
| 卡片「待审核节点」 | `stats.nodes.pending` | **真实** | L16 |
| 卡片「近7日新增节点」 | `stats.nodes.new_7d` | **真实** | L23 |
| 卡片「已发布节点」 | `stats.nodes.published` | **真实** | L29 |
| 卡片「活跃用户」 | `stats.users.active` | **真实** | L36 |

> ✅ 全页诚实，因为 `/admin/stats` 是真正的聚合接口。L93 还专门写明「这些统计来自后端真实 `/admin/stats`，不再展示伪造的最近活动」。**这是其它页面应该效仿的模式。**

---

### 4. 管理端 · 节点管理 AdminPendingNodesPage
**文件**：`frontend/src/pages/admin/AdminPendingNodesPage.vue`

**消费的接口 / hooks**
- `useAdminNodesQuery({ limit: 80, status, keyword })` → `GET /admin/nodes`（L24-28，**limit 固定 80**）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「当前结果」 | `adminNodes.value?.length`（≤80） | **说谎**（标签「当前结果」勉强自洽，但 ≥80 条时会卡在 80，用户以为系统总共就 80 个节点） | 定义 L48，渲染 L159 |
| Hero「待审核」 | `adminNodes.filter(status==='pending').length`（在 ≤80 的数组里 filter） | **说谎**（被 limit:80 截断后再 filter，不是全站待审核总数；与 Dashboard 的 `stats.nodes.pending` 矛盾） | 定义 L49，渲染 L163 |
| Hero「已归档」 | `adminNodes.filter(status==='archived').length`（同上） | **说谎**（同上） | 定义 L50，渲染 L167 |
| 卡片 `N 字` / Book N / Node N | `node.word_count` / `book_id` / `id` | **真实** | L240-242 |

> 待审核数在本页是「≤80 内的 pending 数」，在 Dashboard 是真实 `stats.nodes.pending`，两处会对不上 —— 经典指标说谎症状。

---

### 5. 管理端 · 用户管理 AdminUsersPage
**文件**：`frontend/src/pages/admin/AdminUsersPage.vue`

**消费的接口 / hooks**
- `useAdminUsersQuery({ role, is_active, keyword })` → `GET /admin/users`（L48；**未显式传 limit，依赖后端默认 limit**）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「Visible Users」 | `users.value?.length`（受后端默认 limit 截断） | **说谎（半诚实）**（标签是「Visible Users」可见用户数，但用户会把它当注册总数；真实总数应来自 `/admin/stats` 的 `users.total`） | 定义 L57，渲染 L161 |

> 标签写「Visible Users」是好的自觉，但 hero 上孤零零一个数仍会被读成「站点用户总数」。真实总数其实唾手可得：`stats.users.total` / `active` / `inactive` 都在 `/admin/stats` 里。

---

### 6. 故事册列表 BookListPage
**文件**：`frontend/src/pages/books/BookListPage.vue`

**消费的接口 / hooks**
- `useBooksQuery()` → `GET /story/books`（L8；`fetchBooks` 未传 limit，见 `features/story/api.ts:13-18`）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「Books」 | `books?.length`（依赖后端 `/story/books` 是否分页） | **说谎（条件性）**（若后端 `/story/books` 有默认 limit 则被截断；当前前端不传 limit、也没有 books 总数接口 → 一旦故事册数超过后端默认 limit 就说谎） | L71 |
| Hero「Filter」 | `selectedPhase` 文案 | **真实**（不是计数） | L75 |
| 卡片 Created / ID | `book.created_at` / `book.id` | **真实** | L146-147 |

> 注意：卡片**没有**展示 `book.nodes_count`（`StoryBook` 类型 L39 有该字段），所以「每本书有多少节点」这个本可真实展示的指标在列表页是**缺失**的。

---

### 7. 故事册详情 / 故事树 BookDetailPage
**文件**：`frontend/src/pages/books/BookDetailPage.vue`

**消费的接口 / hooks**
- `useBookQuery(bookId)` → `GET /story/books/{id}`（L30）
- `useStoryTreeQuery(bookId)` → `GET /story/tree?book_id=`（L31，**返回完整树，无 limit**，见 `features/story/api.ts:33-35`）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「节点」 | `flatNodes.length`（拍平完整树） | **真实**（树是全量返回，flatten 后即真实总数） | 定义 L52-53，渲染 L184 |
| Hero「完结」 | `flatNodes.filter(is_ending).length` | **真实** | 定义 L54，渲染 L189 |
| Hero「分歧点」 | `flatNodes.filter(children.length>1).length` | **真实** | 定义 L55，渲染 L192 |

> ✅ 诚实，前提是 `/story/tree` 永远全量返回整棵树（无 skip/limit）。若后端将来给树加分页，这三个数会立刻变成说谎。**建议在后端审计里确认 `/story/tree` 不分页。**

---

### 8. 节点详情 StoryNodePage
**文件**：`frontend/src/pages/story/StoryNodePage.vue`

**消费的接口 / hooks**
- `useNodeDetailQuery(nodeId)` → `GET /story/node/{id}`（L33，返回 `StoryNodeRead`，含真实 `likes_count`/`comments_count`/`children_count`/`is_liked`）
- `useNodePathQuery(nodeId)` → `GET /story/node/{id}/path`（L34）
- `useNodeChildrenQuery(nodeId, { limit: 5 })` → `GET /story/node?parent_id=`（L35，**limit:5**）
- `useInfiniteNodeCommentsQuery(nodeId)` → `GET .../comments`（分页，每页 20）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| 点赞按钮「N 点赞/已赞」 | `node.likes_count` | **真实** | L307 |
| **「子分支（N）」标题** | `children.length`（**limit:5**） | **说谎**（应使用 `node.children_count`；同页 detail 已带真实 `children_count` 却没用在标题上） | L336、空态 L373 |
| 空态「子分支（0）」 | `children?.length \|\| 0` | **说谎**（同上；children 为空可能只是 limit:5 没拉到，但此处实际只在没子节点时显示，影响小） | L373 |
| 子节点卡片 `N 赞/评论/分支` | `child.likes_count` / `comments_count` / `children_count` | **真实**（每个子节点自身的 denormalized 字段） | L361-363 |
| 「评论区（N · 已显示 M）」 | 总数 `node.comments_count`（真实），已显示 `comments.length` | **真实**（优先用 `comments_count`，回退本地长度，逻辑见 L43-47） | L394 |
| 「还剩 N 条 / 已加载全部 N 条」 | `totalCommentsCount - loadedCommentsCount` | **真实**（基于真实 `comments_count`） | L463, L469 |

> 唯一的说谎点是「子分支（N）」标题用了 limit:5 的 children 长度。**修复极简单**：把标题里的 `children.length` 换成 `node.children_count`（已有真实字段）。

---

### 9. 故事线 StoryLineagePage
**文件**：`frontend/src/pages/story/StoryLineagePage.vue`

**消费的接口 / hooks**
- `useNodeLineageQuery(nodeId)` → `GET /story/node/{id}/lineage`（返回从根到该节点的祖先链）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| 各节点「N 赞」 | `item.likes_count` | **真实** | L111, L124 |
| 分支链长度（用于高亮 last） | `lineage.length` | **真实**（lineage 是完整祖先链，不是被 limit 的列表；且这里只用于定位「当前节点」，未作为总数展示给用户） | L68, L87, L129 |

> 本页无说谎指标。

---

### 10. 通知中心 NotificationPage
**文件**：`frontend/src/pages/notification/NotificationPage.vue`

**消费的接口 / hooks**
- `useInfiniteNotificationsQuery()` → `GET /interaction/notifications`（分页，每页 20）
- `useUnreadCountQuery()` → `GET /interaction/notifications/unread-count`（返回 `{ unread_count }`，见 `features/interaction/api.ts:48-50`）

**显示的指标**
| 指标 | 来源 | 分类 | 位置 |
| --- | --- | --- | --- |
| Hero「Total」 | `allNotifications.length`（**仅已加载的页**） | **说谎**（无限滚动只统计已 fetch 的页，不是通知总数；用户滚得越多数字越大） | 定义 L50，渲染 L178 |
| Hero「Unread」 | `unreadCount.unread_count` | **真实**（有专门 count 接口） | 定义 L49，渲染 L182 |
| 「当前筛选结果 N 条」 | `filteredNotifications.length` | **说谎（半诚实）**（只是已加载页里符合筛选的条数，非该类型真实总数） | L228 |

> Unread 是真实的（有 count 端点），Total 没有对应端点 → 说谎。**这正说明：给 list 配套一个 count，就能消灭说谎。**

---

### 11. 组件级

- **CommentList.vue**（`frontend/src/components/interaction/CommentList.vue`）：评论总数显示优先用父级传入的 `commentsCount`（来自 `node.comments_count`），回退本地长度。注释 L9-12 / 逻辑 L31-33 / 渲染 L57、L109、L118 —— **真实**（前提是父级传了 `commentsCount`，不传则退化为不准确）。注：当前 StoryNodePage 用的是内联评论区，未实例化此组件，但组件本身设计是诚实的。
- **StoryTreeInspector.vue**（`frontend/src/components/story/StoryTreeInspector.vue`）：「点赞」`selectedNode.likes_count`（L84）、「子分支」`selectedNode.children.length`（L88）—— **真实**（selectedNode 来自完整故事树，children 是全量子节点）。
- **StoryTreeFlow.vue**：`childCount: children.length`（L130）、`likes_count`（L123）—— **真实**（同样来自完整树）。
- **DiscoveryRail / DiscoveryNodeCard / StoryTreeFlowNode / StoryBranchPath**：只渲染父级传入的 metrics / 路径，`.length` 仅用于「是否为空」判断（如 `items?.length`、`item.metrics?.length`），不作为总数展示 —— **不涉及说谎**。
- **DefaultLayout.vue**：导航未读角标 `unreadCount.unread_count`（L113）—— **真实**。

---

## 说谎指标清单（汇总表）

| # | 页面 | 指标（UI 文案） | 说谎来源 | 被谁截断 | 应改用的真实来源 | 文件:行 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HomePage | Hero「SHOWN · 编辑标记」 | `featuredNodes.length` | discovery/featured limit:4 | featured 全量计数接口 | HomePage.vue:113,305 |
| 2 | HomePage | Hero「SHOWN · 近期入档」 | `latestFeed.length` | discovery/feed limit:4 | feed 全量计数接口 | HomePage.vue:112,309 |
| 3 | HomePage | Hero「SHOWN · 高度关注」 | `trendingNodes.length` | discovery/trending limit:4 | trending 全量计数接口 | HomePage.vue:114,311 |
| 4 | HomePage | 搜索「MATCHED N ENTRIES」 | `searchResults.length` | discovery/search limit:6 | search 命中总数（X-Total-Count） | HomePage.vue:525 |
| 5 | ProfilePage | Hero「Nodes」 | `submittedNodes.length` | story/user/{id}/nodes limit:5 | **`user.nodes_count`（已存在）** | ProfilePage.vue:172 |
| 6 | AdminPendingNodes | Hero「当前结果」 | `adminNodes.length` | /admin/nodes limit:80 | /admin/nodes 总数（带筛选） | AdminPendingNodesPage.vue:48,159 |
| 7 | AdminPendingNodes | Hero「待审核」 | `adminNodes.filter(pending).length` | /admin/nodes limit:80 | **`stats.nodes.pending`（已存在）** | AdminPendingNodesPage.vue:49,163 |
| 8 | AdminPendingNodes | Hero「已归档」 | `adminNodes.filter(archived).length` | /admin/nodes limit:80 | **`stats.nodes.archived`（已存在）** | AdminPendingNodesPage.vue:50,167 |
| 9 | AdminUsers | Hero「Visible Users」 | `users.length` | /admin/users 默认 limit | **`stats.users.total`（已存在）** | AdminUsersPage.vue:57,161 |
| 10 | BookListPage | Hero「Books」 | `books.length` | /story/books 默认 limit（若有） | books 总数接口 | BookListPage.vue:71 |
| 11 | StoryNodePage | 「子分支（N）」标题 | `children.length` | story/node limit:5 | **`node.children_count`（已存在）** | StoryNodePage.vue:336,373 |
| 12 | NotificationPage | Hero「Total」 | `allNotifications.length` | 无限滚动仅已加载页 | 通知总数接口 | NotificationPage.vue:50,178 |
| 13 | NotificationPage | 「当前筛选结果 N 条」 | `filteredNotifications.length` | 同上 | 按类型分组的总数 | NotificationPage.vue:228 |

**可零成本修复（真实字段已在前端数据里，只是没用对）**：#5、#7、#8、#9、#11。这五处不需要任何后端改动，只需把数据源换成已存在的 denormalized / stats 字段。

---

## 前端真正需要后端补什么

1. **list 接口的总数（最高优先级）**
   通用方案二选一：
   - 在所有分页 list 接口返回 `X-Total-Count` 响应头；或
   - 改返回包络 `{ items: [...], total: N, skip, limit }`。
   覆盖：`/discovery/featured|feed|trending|search`、`/admin/nodes`、`/admin/users`、`/story/books`、`/interaction/notifications`、`/story/user/{id}/nodes`、`/story/node?parent_id=`（子节点）。
   这一项能直接消灭清单里 #1-4、#6、#10、#12、#13。

2. **复用已有 denormalized / stats 字段（无需后端改动，前端自查）**
   - ProfilePage「Nodes」→ 用 `user.nodes_count`（`/auth/me` 已返回）。
   - StoryNodePage「子分支（N）」→ 用 `node.children_count`（节点详情已返回）。
   - AdminPendingNodes「待审核 / 已归档」→ 用 `/admin/stats` 的 `nodes.pending` / `nodes.archived`（需在该页额外调用 `useAdminStatsQuery`）。
   - AdminUsers「Visible Users」→ 改为展示 `/admin/stats` 的 `users.total`（同样需在该页调用 stats）。

3. **建议后端确认的不变量**
   - `/story/tree` **必须全量返回整棵树、不分页**，否则 BookDetailPage 的「节点/完结/分歧点」三个真实指标会变成说谎。
   - 用户公开资料应保证 `nodes_count` / `likes_count` 在 `/auth/me`（以及未来的他人主页接口）上始终被填充，供 ProfilePage 替换 `submittedNodes.length`。

4. **可选增强**
   - discovery 各栏目（featured/latest/trending）若要在首页 hero 展示真实站点总数，需要轻量 count 端点（或一个聚合的「站点概览」接口，类似 `/admin/stats` 的公开版）。
   - `/discovery/search` 返回命中总数，让首页「MATCHED N」诚实。
