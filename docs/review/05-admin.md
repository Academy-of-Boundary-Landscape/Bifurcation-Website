# 后台管理（Admin）前端审查 — 05

审查范围：
- `frontend/src/pages/admin/AdminDashboardPage.vue`
- `frontend/src/pages/admin/AdminPendingNodesPage.vue`
- `frontend/src/pages/admin/AdminBooksPage.vue`
- `frontend/src/pages/admin/AdminUsersPage.vue`
- `frontend/src/features/admin/{api.ts,queries.ts}`
- `frontend/src/router/index.ts`（`requiresAdmin` 守卫）

对照文档：`docs/frontend/visual-style.md`、`docs/frontend/data-layer.md`、`docs/backend/features.md`、`docs/followups.md`。

---

## 概览

整体质量较高。数据层收口到位：四个页面都消费 `features/*/queries.ts` 暴露的 hook，没有页面级直写请求；query key 全部来自 `features/queryKeys.ts`；mutation 后的缓存失效基本精确（审核失效 `storyNode/storyTree/pendingNodesRoot/adminNodesRoot`，更新用户失效 `adminUsersRoot/adminStats`）。仪表盘统计严格对齐后端 `GET /admin/stats`（字段 `users.{total,active,inactive,new_7d}` / `nodes.{total,pending,published,archived,new_7d}` 与后端 `admin.py:241-273` 一一对应），不再有伪造指标。视觉上延续了同一套 `ui-shell-*` / `ui-panel-section` / `ui-metric-card` 语言，信息密度高于前台，符合"操作台"定位。

主要问题集中在三类：(1) **破坏性/封禁操作没有二次确认**，封禁、停用、归档全部一键生效；(2) **列表没有真正的分页**，靠硬编码 limit 截断且无总数，存在"指标说谎"风险（与最近一次 commit 修的同类问题同源）；(3) **路由守卫只有客户端检查**，且 `banned` 用户与 `isAdmin` 的判定存在边界缺口。可访问性方面表单 `label` 包裹得不错，但状态标签仅靠颜色、缺少 `aria` 与键盘可达性补强。

---

## 发现

### 【高】封禁/停用用户无二次确认，且为破坏性操作
`frontend/src/pages/admin/AdminUsersPage.vue:107-140`、`:281-292`

将角色改为 `banned`、或把 `活跃状态` 关掉（停用账户），都是高风险操作，但 `handleSaveUser` 直接 `updateUser` 提交，没有任何 `n-popconfirm` / `dialog` 二次确认。视觉规范明确要求"危险按钮使用冷红，只在真正高风险操作中出现"（visual-style.md 危险按钮一节），而当前"保存修改"是普通 primary 按钮，封禁和改简介用同一个按钮、同一种视觉权重。管理员误点即生效，且没有"撤销"反馈。
**建议**：把"封禁/停用"从普通保存里拆出来，做成独立的危险操作（冷红、带 `n-popconfirm` 文案如"确认封禁该用户？ta 将无法继续参与业务"）；或在 `handleSaveUser` 检测到 `role` 变为 `banned` 或 `is_active` 由 true→false 时弹确认。

### 【高】节点归档无确认 + 仅靠 message 反馈
`frontend/src/pages/admin/AdminPendingNodesPage.vue:110-147`

归档（驳回）是把节点 `* -> archived` 的破坏性流转（features.md 第 6 节），会给作者发驳回通知。当前只校验"归档必须填原因"（:114-117，这点很好），但应用按钮本身无二次确认，且按钮是普通 primary，不是危险样式。对比之下后端把它当审核驳回处理（`story_nodes.py:150-153` 发 `REJECTED` 通知）。
**建议**：归档动作加 `n-popconfirm`，并把"应用→归档"时的按钮渲染为危险态；发布（无损、可逆性高）保持普通态，形成"操作优先级分明"的层次。

### 【高】列表无真正分页，靠硬编码 limit 截断且无总数（指标可能说谎）
`frontend/src/pages/admin/AdminPendingNodesPage.vue:20-27,47-49`、`AdminUsersPage.vue:39-57`、`features/admin/api.ts:8-48`

- 节点页固定 `limit: 80`（`:21`），后端 `limit` 上限 200（`admin.py:90`）。超过 80 个待审/归档节点时列表静默截断，**没有"下一页"也没有总数**。Hero 区"当前结果 / 待审核 / 已归档"三个指标（`:47-49,164-172`）是对**已截断的 80 条**做 `filter().length`，并非全库真实计数——这正是 `docs/followups` 同源、最近一次 commit "修复指标说谎" 想消灭的模式，这里又出现了一次。
- 用户页 `useAdminUsersQuery(queryParams)` 完全不传 `skip/limit`，后端默认 `limit=50`（`admin.py:196`）。第 51 个用户起不可见，"Visible Users" 指标（`AdminUsersPage.vue:57,161`）同样只是"前 50 条"，名称虽诚实（Visible）但管理员无法翻页看到其余用户。
- 仪表盘里有真实总数（`stats.nodes.pending` / `stats.users.total`），但管理页不引用它，导致仪表盘和管理页的"待审核"数字在数据量大时会对不上。

**建议**：引入分页（`skip/limit` + `n-pagination`），列表标题用 `stats` 的真实总数而不是当前页 `length`；或至少在命中 limit 时显示"仅展示前 N 条，请用筛选缩小范围"的明确提示，避免静默截断 + 假指标。

### 【高】管理员权限仅客户端守卫，且 `banned` 用户判定有缺口
`frontend/src/router/index.ts:111-133`、`frontend/src/stores/auth.ts:40`

`requiresAdmin` 只在 `beforeEach` 用 `authStore.isAdmin`（`role === 'admin'`）判断，纯客户端。这本身可接受（后端 `get_current_admin` 仍是真正护栏），但有两点要注意：
1. **后端必须强制**：所有 `/admin/*` 已用 `Depends(deps.get_current_admin)`（确认于 `admin.py:125,155`），守卫被绕过也安全——应在文档/注释里明确"前端守卫仅为 UX，权限以后端为准"。
2. **`banned` / `is_active=false` 用户**：守卫只拦非 admin 访问 `/admin/*`，但对全站其它 `requiresAuth` 路由，`isBanned`（auth.ts:42）和 `is_active` 均未被守卫消费。被封禁/停用用户只要本地仍持有有效 token，前端不会拦截其访问与写操作入口（最终靠后端 401/403）。这与 `followups.md 3.3` 关注的 banned 用户处置方向一致，目前前端侧无任何呈现。
**建议**：在守卫里对 `isBanned` 做统一拦截/提示；admin 路由保留客户端守卫但在代码注释标注后端为准。

### 【中】审核工作台命名/文件与实际职责不符，易误导维护者
`frontend/src/router/index.ts:78`、`AdminPendingNodesPage.vue`

路由 `admin-nodes` 指向的组件文件名是 `AdminPendingNodesPage.vue`，但它实际用 `useAdminNodesQuery`（全部节点），并非 `usePendingNodesQuery`。`features/admin` 里 `usePendingNodesQuery` / `fetchPendingNodes`（queries.ts:29-39, api.ts:40-48）**完全没有被任何页面使用**，是死代码。文件名与职责漂移，后续维护者容易误判。
**建议**：把文件重命名为 `AdminNodesPage.vue`，并删除未使用的 `usePendingNodesQuery` / `fetchPendingNodes`（或在仪表盘"待审核"卡片真正复用它）。

### 【中】节点筛选状态切换后无防抖、keyword 直接打 query
`frontend/src/pages/admin/AdminPendingNodesPage.vue:194-199`、`AdminUsersPage.vue:201-208`

keyword 输入通过 `v-model` / `@update:value` 直接驱动 `computed` query params，每次按键都会触发新的 query key → 新请求（TanStack 会缓存但仍每键一发）。在数据量大、网络一般时会产生抖动和多余请求。
**建议**：keyword 加 `useDebounce`（VueUse）或显式"搜索"按钮再提交。

### 【中】用户角色/状态标签直接渲染英文枚举，违反前台中文化与标签语义稳定
`frontend/src/pages/admin/AdminUsersPage.vue:244-249`

角色标签直接显示 `{{ user.role }}`（admin/writer/banned）、状态显示 `active/inactive`，而同页筛选项却是中文（"管理员/作者/封禁"，`:51-55`）。同一页面两套语言，且 visual-style.md 要求"状态标签视觉语义要稳定"。此外 `banned` 角色用 `getRoleType` 返回 `default`（灰），与"封禁"应有的告警语义不符——封禁是负面状态，灰色弱化了它。
**建议**：复用已有的 `roleOptions` label 做中文映射；`banned` 用 `error`/`warning` 冷色系而非 default。

### 【中】节点页 hero 指标与筛选交互割裂，"在树中定位"对 pending 节点可能无效
`frontend/src/pages/admin/AdminPendingNodesPage.vue:106-108,265-267`

`focusNodeTree` 跳到 `book-detail?focusNodeId=`，但待审核（pending）节点通常不在公开故事树渲染范围内，跳过去可能定位不到，给管理员造成"按钮坏了"的错觉。
**建议**：对 `status === 'pending'` 的节点隐藏或禁用"在树中定位"，或确保 book-detail 在管理员视角能渲染 pending 节点。

### 【中】Books / Users / Nodes 三页 `editState`/`draftState`/`nodeReason` 随筛选刷新不清理
`frontend/src/pages/admin/AdminBooksPage.vue:29-43,136-152`、`AdminUsersPage.vue:26-37,83-96`

`draftState` / `editState` 以 `id` 为 key 累积，列表 refetch（改筛选、刷新）后旧 draft 仍残留在内存。若同一 id 的实体在后台被改动，再次展开会拿到 `ensureDraft` 早先缓存的旧值（因为 `if (draftState.value[user.id]) return`，:84），显示与服务器不一致。
**建议**：保存成功后清除该 id 的 draft，或在 query 数据更新时使旧 draft 失效。

### 【低】可访问性：状态仅靠颜色 + 缺少操作区 aria 标注
`AdminPendingNodesPage.vue:244-247`、`AdminUsersPage.vue:244-249`、`AdminBooksPage.vue:388-391`

状态/角色/阶段 `n-tag` 全部仅以颜色区分（success/error/warning/default），色弱用户难分辨"已发布 vs 已归档"。文本内容能补救一部分，但例如节点页同时存在多个 `type="default"` 的灰标签（Book/Node/字数）和"已归档"灰标签时层次不清。可展开/折叠的卡片操作（"展开正文"/"展开编辑"）没有 `aria-expanded`。
**建议**：状态标签加图标或文字前缀；折叠按钮补 `aria-expanded` / `aria-controls`。

### 【低】Empty state 与 Loading 叠加时的体验
`AdminPendingNodesPage.vue:221-222`、`AdminUsersPage.vue:221-222`、`AdminBooksPage.vue:371-372`

`n-empty` 放在 `n-spin` 内部，首次加载时 `adminNodes` 为 `undefined`，`!adminNodes?.length` 为真，会在 spin 转圈的同时短暂闪出"没有节点"空状态，再被数据替换。
**建议**：空状态判断加 `!isLoading &&`，避免加载态误显空文案。

### 【低】错误处理只走 message，无重试/无错误态展示
四个页面的 query（`useAdminStatsQuery` 等）都没有消费 `isError`/`error`。请求失败时页面停在 spin 结束后的空白或空态，管理员不知道是"真没有"还是"加载失败"。mutation 侧有 `onError` toast（较好），但读取侧缺失。
**建议**：列表区加 `isError` 分支，显示错误文案 + "重试"按钮（调用 `refetch`）。

### 【低】审核 mutation 失效未覆盖 `adminStats`
`frontend/src/features/admin/queries.ts:87-93`

`useAuditStoryNodeMutation` 审核后失效了 `pendingNodesRoot/adminNodesRoot/storyNode/storyTree`，但**没有失效 `adminStats()`**。发布/归档会改变 `nodes.pending`/`published`/`archived` 计数，仪表盘"待审核节点"在审核后不会自动更新（除非重进页面）。对比 `useAdminUpdateUserMutation`（:74-77）就正确失效了 `adminStats`。
**建议**：在审核 `onSuccess` 里追加 `queryClient.invalidateQueries({ queryKey: queryKeys.adminStats() })`。

---

## 优先级建议（前 3）

1. **破坏性操作加二次确认 + 危险视觉**（封禁/停用用户、归档节点）。当前一键生效、无确认、无危险样式，是最高风险项，同时违反 visual-style 的危险按钮规范。
2. **修列表分页与指标真实性**。节点页/用户页靠硬编码 limit 静默截断，hero 指标对截断后数组做 `.length`，是"指标说谎"模式复发；改用 `stats` 真实总数 + 分页，或至少给出截断提示。
3. **收口节点页职责与审核缓存失效**：重命名 `AdminPendingNodesPage`→`AdminNodesPage`、删除未用的 `usePendingNodesQuery`/`fetchPendingNodes`，并在审核 mutation 补 `adminStats` 失效，让仪表盘与管理页数字一致。
