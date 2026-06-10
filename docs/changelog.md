# Changelog

## 2026-06-11

### CI/CD 安全加固（设计见 `docs/superpowers/specs/2026-06-11-cicd-security-hardening-design.md`，计划见 `docs/superpowers/plans/2026-06-11-cicd-security-hardening.md`）

- **新增安全扫描工作流 `security.yml`**：集成 pip-audit（Python 依赖漏洞）+ npm audit（JavaScript 依赖漏洞）+ gitleaks（代码仓库敏感信息），仅报告不拦截；扫描在 push/PR 时触发 + 每周定时执行，便于持续监控安全状态。
- **`ci.yml` backend job 加固**：新增 Trivy 镜像扫描（容器镜像漏洞扫描），SARIF 格式上传到 GitHub Security 页面；新增 pip 缓存，加速重复构建。
- **`ci.yml` deploy job 串行化控制**：加入并发锁（concurrency group），确保同时到达的部署按序执行，避免多个部署并行进行导致的资源争用或部署冲突。
- **`deploy.sh` 回滚策略升级**：从假回滚（仅日志记录）改为真实回滚，失败时自动捕获旧镜像 ID 并恢复上一版本，随后执行二次健康检查确认回滚成功，提高生产稳定性。

## 2026-06-03

### 限流（两层，来自 `docs/followups.md` §3.1）

- **应用层（slowapi，按用户/IP，内存存储）**：新增 `backend/app/core/rate_limit.py`（limiter + key 函数 + 429 处理器 + 阈值常量）。点赞 `60/min`、评论 `6/min` 按登录用户限流（`get_current_user` 把 `user.id` 写进 `request.state`，供 key 函数读取）；SSO 换登录态 `10/min` 按真实客户端 IP 限流（优先取 nginx 写入的可信 `X-Real-IP`，避免客户端伪造 `X-Forwarded-For` 首跳绕过）。429 返回统一 `{"detail": "操作过于频繁，请稍后再试"}` + `Retry-After` 头（直接从触发的限速窗口取秒数，绕开 slowapi 默认关闭的 header 注入）。
- **网络层（nginx，仅写操作）**：`deploy/nginx.conf` 与 `nginx.example.conf` 加 `map $request_method` → 写方法（POST/PUT/PATCH/DELETE）按 IP 计数、读请求 key 为空跳过；`limit_req_zone … rate=20r/s` + `limit_req … burst=40 nodelay`，`limit_req_status 429`。属手动部署物，不在 CI。
- **前端 429 提示**：抽出共享主题 `frontend/src/theme.ts`（App.vue 复用）；新增 `services/notify.ts` 用 `createDiscreteApi` 在拦截器（Vue setup 外）弹全局提示，3s 去重；`services/http.ts` 加 429 分支，复用 `ApiErrorResponse` 类型且不吞错误。
- **测试**：`backend/tests/test_rate_limit.py`——key 函数单测 + 评论限流 429 集成测试（前 6 条 200、第 7 条 429、校验 body 与 `Retry-After: 60`）；`test_support.py` 默认 `limiter.enabled=False` 防止误伤既有用例并避免跨用例累积。
- 验证：后端 `pytest` 39 passed；前端 `vue-tsc` + `build` 通过。范围外（未做）：建节点/上传限流、Redis 共享存储（多 worker 时再换）。

## 2026-06-02

### 诚实指标（前后端协同，来自 `docs/backend-review/`）

- **Phase A 零成本（前端）**：ProfilePage「Nodes」改用 `user.nodes_count`、StoryNodePage「子分支(N)」改用 `node.children_count`、后台节点/用户 hero 改用 `/admin/stats`——不再用被 limit 截断的当前页 `.length` 冒充总数。
- **Phase C 计数完整性（后端，TDD）**：点赞/评论/子节点 6 处计数改为原子 SQL（`x=x±1`，减法 `case` 防负），消除并发丢更新；`children_count` 统一为"非归档子节点"并在审核归档/恢复时增减；`/auth/me` 的 `nodes_count` 对齐为只数已发布；`/admin/stats` 活跃用户排除封禁并新增 `banned`；新增对账脚本 `backend/scripts/recount.py`。
- **Phase B 总数契约（前后端）**：列表端点保持裸 `List` body，通过响应头 `X-Total-Count` 暴露真实总数（discovery×4 / notifications / books，CORS 已 expose）；前端 `getList<T>` 读取，修正首页 telemetry、搜索「MATCHED N」、通知页「Total」、书列表「Books」。
- 验证：后端 `pytest` 35 passed（含原子计数 / 排除封禁 / X-Total-Count 集成断言）；前端 `type-check` + `build` 通过。

### 前端代码清洗

- 前端代码清洗（来自 `docs/review/00-overview.md` 主题 A/F/G）：删除 20 个文件、净减约 3700 行，`npm run type-check` 与 `npm run build` 均通过。删除前对每个符号都用 `git grep` 二次验证零引用，并纠正了审阅的两处误报（`UserAvatar.vue` 实际在用已保留；不存在所谓"仓库根 frontend/ 未跟踪副本"）。
- 删除已验证零引用的整组组件：`components/common/{ConfirmDialog,EmptyState,ErrorBlock,LoadingBlock,PageTitle,AppFooter}.vue`、整个 `components/editor/*`（5 个，含带 `alert()`/坏 `DraftGuard` 的死实现）、`components/story/StoryTreePanel.vue`。
- 删除零引用的 store / util / composable：`stores/counter.ts`、`stores/ui.ts`、`utils/validation.ts`（整文件，写作页有自己的内联校验）、`composables/usePageTitle.ts`。
- 局部删死：`utils/storage.ts` 移除未用的 `StorageManager` 类（保留在用的 `getStorage/setStorage/removeStorage`）；`services/http.ts` 移除未用的 `useMessage` import；`features/admin/*` 移除死 hook `usePendingNodesQuery` 与 `fetchPendingNodes`（页面用的是 `useAdminNodesQuery`）；`uno.config.ts` 移除违反黑白风格且零引用的 `accent: '#8b5cf6'`。
- 清理 `types/*` 中 18 个零引用死类型，并顺带去掉 `ApiResponse`/`PaginatedResponse`/`ApiErrorResponse` 在 `api.ts` 与 `models.ts` 间无人消费的重复定义（消费方 `error-handler.ts` 指向 `api.ts` 版本，故 `models.ts` 副本为死代码）。
- 清理仓库历史噪声（git 移除）：`frontend-temp/`、根目录 `cline.md`、`frontend/DEVELOPMENT_PROGRESS.md`（过期进度文档，且引用了已删除的 `cline.md`）。
- 修复断裂的正文页面包屑：`StoryNodePage.vue` 模板早已使用 `<story-branch-path>` 却从未 import，导致面包屑静默渲染空白；现已正确引入 `StoryBranchPath`，并把该组件的紫色/硬编码色与无效点击逻辑收回到黑白终端 token 风格。
- 统一节点状态枚举中文展示：新增单一来源 `utils/storyStatus.ts` 的 `storyStatusLabel()`，替换 `StoryTreeFlowNode` 的内联映射，并在此前仍渲染英文裸 `status` 的 Inspector、StoryNodePage、StoryLineagePage、StoryCreateConfirmModal、ProfilePage、AdminPendingNodesPage（去掉其重复的本地 `statusLabel`）统一复用。
- 新增工程纪律文件 `CLAUDE.md`（编程纪律、数据层/视觉风格约定、superpowers 技能提醒）；新增前端审阅意见 `docs/review/`（6 分册 + 总览）。

## 2026-04-02

- 彻底移除本地 `is_verified` 用户字段：后端用户模型、Schema、SSO 同步、初始化脚本、前端用户类型与测试契约都不再依赖“邮箱已验证”这条旧本地注册语义；在当前 Casdoor SSO 方案下，站内权限只取决于本站 token、`is_active` 和本地角色。
- 为“创建后续节点”加入统一的轻确认弹窗：新增 `StoryCreateConfirmModal.vue`，在故事树检视器、书页主操作区、节点详情页和分支阅读页进入写作前，先展示当前上下文、摘要和提交说明，再进入独立写作页，避免直接跳转带来的突兀感。
- 统一写作页路由语义：新增 `buildStoryWriteRoute()`，所有“创建后续节点”入口都统一跳到“`bookId + parentId` 上下文”而不是任何未来节点 ID；`StoryWritePage.vue` 也同步收紧了 `parentId` 解析，避免 query 形态抖动导致上下文错乱。
- 新增管理员全节点管理能力：后端补上 `GET /api/v1/admin/nodes`，支持按状态、作者、故事册和关键词筛选；前端将原 `AdminPendingNodesPage.vue` 升级为“节点管理工作台”，管理员现在可以查看全部节点、定位故事树中的节点，并直接发布或归档，不再只能看到 pending 队列。
- 修复故事树在当前视角下因父节点缺失导致子树直接消失的问题：`build_memory_tree()` 现在会把“父节点未出现在结果集里但当前节点可见”的节点提升为局部 root，避免管理员或作者在可见性过滤后看不到本应可见的节点。
- 修复故事树可见性与其他登录接口不一致的问题：`get_current_user_or_none()` 不再沿用旧邮箱验证语义过滤已登录用户，避免已登录管理员或作者在 `/story/tree`、`/story/node/{id}` 等可选鉴权接口里被误判成游客，导致 archived/pending 节点被错误过滤。
- 继续把故事册后台接满后端现有接口：`AdminBooksPage.vue` 现在除了新建故事册、切换阶段和开关创作外，还支持展开编辑已有故事册的标题、简介、封面、阶段、创作开关和时间窗口，真正覆盖 `PATCH /api/v1/story/books/{book_id}` 的主要能力。
- 继续把管理员前端补齐到后端现有 API：重做 `AdminUsersPage.vue`，正式接入 `/admin/users` 的角色筛选、活跃状态筛选、关键词搜索，以及 `/admin/users/{user_id}` 的角色/激活状态/用户名/简介/头像更新，不再停留在只读列表。
- 重做 `AdminDashboardPage.vue`，去掉后台里原先伪造的“最近活动”示例数据，改成只展示来自 `/admin/stats` 的真实统计和后台主操作入口，让管理员首页回到“真实概览 + 明确入口”的职责。
- 完善管理员核心页面：重做 `AdminBooksPage.vue`，补上可直接创建故事册的正式表单，支持标题、简介、封面、阶段、创作开关和时间窗口配置；同时继续保留对现有故事册的阶段切换与创作开关控制。
- 重做 `AdminPendingNodesPage.vue` 为实际可用的审核工作台：待审核节点现在支持摘要查看、正文展开/收起、填写驳回原因、直接通过审核、驳回归档和跳转详情页，不再依赖浏览器 `prompt()` 做驳回说明。
- 后端数据库引擎日志改为可配置：新增 `SQL_ECHO` 环境变量，默认关闭 SQLAlchemy/SQLite 的原始 SQL 输出，避免开发时控制台被大量 `BEGIN/SELECT/ROLLBACK` 噪音淹没；如需排查数据库行为，再显式设为 `true`。
- 根据 Casdoor 官方文档收口管理员 claim 约定：后端默认不再优先猜测 `groups`，改为以 `roles/role` 作为管理员同步来源；同步更新 `.env.example`、`backend-setup.md` 与 `backend-features.md`，明确当前站点应使用 Casdoor 角色来表达“是否管理员”。
- 为 Casdoor SSO 的 `state` 链路补充前后端日志，并放宽前端本地 `sessionStorage` 校验为“记录并提示、后端最终校验”：前端现在会记录登录发起时的 `origin/state/redirectTo`、回调页收到的参数以及 state 不匹配时的本地元信息；后端会记录 state 解码和 exchange 开始时的摘要，便于排查 `localhost/127.0.0.1` 混用、重复点击登录或回调页刷新导致的假性 state 失配。
- 继续收口前端旧残留：删除未再引用的旧版 `components/common/AppHeader.vue`，避免其和当前正式使用的 `layouts/DefaultLayout.vue` 继续并存，减少后续头部改动时误改旧组件的风险。
- 清理前端类型与 API 边界中的重复定义：`types/models.ts` 中重复的 `UserNotificationsSummary`、`UserNodeStatsResponse`、`AdminNodeStatsResponse`、`StoryBookNodesCountResponse` 已合并为单一定义；`features/story/api.ts` 中越界的通知摘要请求也已移除，保持 story feature 只承载故事资源。
- 将 `ProfilePage.vue` 继续收回当前黑白终端式设计系统：去掉旧的紫色私有样式和零散结构，改为统一的 `ui-shell` 页面骨架、资料面板、元信息卡和投稿列表卡片，同时保留现有数据层与注册时间显示逻辑不变。
- 重做顶部导航栏 `DefaultLayout.vue`：补上移动端真实主导航、统一已登录用户入口、管理员快捷入口与更清晰的当前区段提示，同时把头部交互和边框/按钮语言收回到现有黑白终端式设计系统，不再依赖旧的 emoji 式下拉菜单。
- 继续收口顶部导航按钮职责：主导航现在只负责页面切换，通知/审核收为右侧工具入口，用户下拉只保留账号相关动作，避免同一功能在主导航、工具区和下拉菜单里重复出现，降低头部按钮层级混乱。
- 修复个人中心“我的投稿”错误命中 `/story/node?author_id=...` 导致 422 的问题；前端用户投稿列表现在改为请求后端正式接口 `/api/v1/story/user/{user_id}/nodes`，避免把用户列表查询误打到“按父节点查子分支”的节点路由上。
- 修复个人中心注册时间显示逻辑：后端 `UserProfileResponse` 现在正式返回 `created_at/updated_at`，前端 `ProfilePage.vue` 改为使用统一的日期时间格式化逻辑显示注册时间，并用 `watch` 同步异步加载后的用户资料到表单状态。
- 重做通知页 `NotificationPage.vue`：从原始的消息卡片堆叠改成统一的“状态面板 + 过滤条 + 通知流”结构，补上更清晰的未读态、通知类型徽标、统一时间格式和更可靠的单条/全部已读交互，并收回到现有黑白终端式设计系统。
- 清理通知链路残留：删除未再使用的 `NotificationBell.vue` 和 `NotificationPanel.vue`，避免旧的彩色弹层组件继续和当前正式通知页并存，后续通知前端只保留一套正式实现和一套数据层。
- 修正 Casdoor OIDC 默认配置：后端不再默认请求错误的 `/.well-known/jwks.json`，改为按 Casdoor 官方路径推导 `jwks`，并在存在 `CASDOOR_APPLICATION_NAME` 时自动使用 application-specific `issuer/jwks`；同时收紧前后端 SSO 失败提示，方便直接定位 `redirect_uri`、JWKS 或 token 校验问题。
- 补上 discovery 的第一条运营可控闭环：后端新增 `GET /api/v1/discovery/featured`，按 `is_featured + feature_rank + published_at` 返回已发布精选节点；前端首页同步新增“精选节点”发现栏，并将其纳入 `features/discovery/*` 与共享 query key 体系。
- 为精选 discovery 能力补充后端单元测试与 SQLite HTTP 集成测试，覆盖“只返回已发布精选节点”和排序行为；同时更新 `docs/discovery-rail-contract.md` 与 `docs/frontend-data-layer-guide.md`，把 `featured` 明确纳入当前 discovery 契约。
- 新增通用发现栏组件 `DiscoveryRail.vue` 与通用节点推荐卡 `DiscoveryNodeCard.vue`，并补充 `frontend/src/types/discovery.ts` 作为前端发现区统一展示契约；首页的“最新更新 / 热门节点 / 搜索结果”开始复用同一套结构而不是各写一遍。
- 新增 `docs/discovery-rail-contract.md`，约定前端发现栏标准数据结构，以及后端未来扩展精选、榜单、推荐接口时建议采用的 section 包装格式，避免后续每个推荐区都重新发明响应结构。
- 将后端已有的 discovery 能力真正接到前端首页：新增 `frontend/src/features/discovery/api.ts` 与 `queries.ts`，把 `/discovery/feed`、`/discovery/trending`、`/discovery/search` 纳入统一数据层，并让 `HomePage.vue` 开始显示“最新更新 / 热门节点 / 节点搜索”三块发现内容。
- 更新 `docs/frontend-data-layer-guide.md`，将 discovery 资源正式纳入前端统一数据层约定，说明首页发现区也应通过 `features/*/api.ts` 与 `features/*/queries.ts` 组合，而不是页面直写请求。
- 开始把高规则密度的后端业务链路下沉到 `backend/app/services/`：新增 `story_nodes.py` 与 `interactions.py`，将“创建节点、审核节点、点赞、评论创建”从路由层抽出，保持现有 API 协议不变但降低 `story.py` / `admin.py` / `interaction.py` 的职责耦合。
- 同步更新后端总览与缺口文档，明确当前服务层已不再只有 SSO，后续整理方向应继续围绕 service 层扩展，而不是把新业务逻辑继续堆回路由文件。
- 补充一轮基于 SQLite 的后端 HTTP 集成测试，真实覆盖 JWT 鉴权、故事树可见性、评论/点赞落库和管理员审核链路，降低只靠 mock 测试带来的偏差。
- 继续补齐 interaction 相关后端测试，覆盖点赞、评论、未读通知统计、单条已读和全部已读；当前 `backend/tests/` 已能覆盖认证、故事、审核、发现和互动的关键主链路。
- 将 `app/core/security.py` 中的 token 过期时间生成改为 timezone-aware UTC，消除测试运行时的 `datetime.utcnow()` 弃用警告。
- 新增 `backend/tests/` 的首批后端单元测试，覆盖 SSO 用户同步、管理员 claim、邮箱自动绑定冲突、节点可见性、续写限制和管理员审核通知等关键链路，并确认可通过 `python -m unittest discover -s tests -v` 运行。
- 修复后端 ORM 中两处真实关系歧义：`User.nodes` 与 `User.comments` 现在都显式声明 `foreign_keys`，避免 `StoryNode.reviewed_by` 和 `StoryComment.deleted_by` 引入的 SQLAlchemy mapper 歧义。
- 新增 `docs/backend-testing-guide.md`，明确说明自动化测试不连接真实 Casdoor，而是 mock claims 与换码结果；真实 Casdoor 留给手工联调和冒烟测试。
- 基于当前后端源码重新核对根目录文档，修正 `backend-setup.md`、`backend-api.md`、`backend-features.md` 中关于管理员初始化、SSO 角色同步、故事接口列表和管理员统计结构的漂移描述。
- 修正 `backend-overview.md` 中已删除模型与旧认证状态的陈述，并将 `casdoor-callback-setup.md` 的本地回调示例统一到测试环境使用的 `127.0.0.1:5174`。
- 将 `casdoor-sso-migration-plan.md` 明确标注为迁移背景与阶段性规划文档，避免继续被误读为当前实现状态。
- 新增 `docs/backend-gap-review.md`，记录本轮后端代码与文档一致性检查结果，并从功能角度梳理当前仍缺的能力，重点包括测试、PKCE、会话能力、迁移体系和后台运维能力。

## 2026-04-01

- 收紧前端故事树与节点详情相关页面的类型定义，减少 `any` 的使用，并让节点/评论数据结构继续对齐现有前后端模型。
- 修复 `ProfilePage.vue` 的头像上传事件类型，改为使用 Naive UI 的 `UploadOnChange`，避免上传回调继续以宽松参数接收文件数据。
- 修复 `NotificationPage.vue` 的路由按钮绑定错误，并重新运行 `frontend` 下的 `npm run type-check`，确认当前前端类型检查通过。
- 重写 `docs/frontend-tree-experience-plan.md`，将前端草案收口为统一版本，明确以“整棵树画布 + 右侧节点检视器”为核心页面结构，并统一阅读体验、结构探索与创作入口的关系。
- 清理一批前端杂项 TypeScript 与模板问题，包括错误的路由绑定、过宽的错误处理、模板内匿名函数和管理页/通知页中的低质量事件写法，为后续正式重做故事树核心交互前先收口代码质量。
- 将 `BookDetailPage` 改造成第一版故事树导航台骨架：保留可拖拽缩放的主画布，新增右侧节点检视器、作品概览统计、节点选中联动，以及从选中节点进入正文、完整分支阅读和创作入口的基础链路。
- 修复故事树主链路中的几个断点：连续阅读页点赞现在会命中实际点击的章节；正文页和连续阅读页增加“返回故事树并聚焦当前节点”；导航台支持读取 `focusNodeId` 保持上下文；树画布拆分了加载态和空态；未实现的“编辑节点”入口暂时下线，避免继续跳入无效的 `mode=edit`。

## 2026-03-26

- 新增 `docs/casdoor-sso-migration-plan.md`，审阅后端认证文档与代码，确认当前系统仍是本地 JWT + 本地密码体系。
- 调整故事树页面的可视化细节：连线由直线改为更柔和的曲线，节点悬浮检视卡现在支持显示中文元信息与最多三个后续分支名称；同时重写树的节点排布逻辑，修复单子节点链路被排成同一水平线导致“连线像没渲染”的问题，让单子节点场景改为更明确的上下递进布局。
- 记录 Casdoor SSO 的推荐迁移路线：采用“Casdoor 负责身份认证，本站保留本地用户与本地 JWT”的兼容方案，避免一次性重写全部业务鉴权。
- 标记现有后端认证文档存在过期和与代码不一致的问题，后续登录迁移应以 `/docs` 下文档为准。
- 后端新增 Casdoor SSO 第一阶段骨架：配置项、SSO 服务层、`/api/v1/auth/sso/login-url`、`/api/v1/auth/sso/exchange`，并保持业务接口继续使用本站本地 JWT。
- 本地 `users` 模型新增 SSO 映射字段，`hashed_password` 改为可空，为逐步下线本地密码登录做准备。
- 新增 `backend/scripts/migrate_add_sso_columns.py`，为已有数据库补齐 SSO 映射字段和索引，避免直接查询 `users` 时因缺列报错。
- 删除 `backend` 目录下 `docs/` 之外的旧后端文档与过期接口导出，包括旧版功能清单，避免继续误导后续开发与 SSO 迁移。
- 重写 `/docs` 下的后端文档，补充后端概览、启动配置、当前 API 与业务规则说明，并统一到新的 SSO + 本地会话模型。
- 清理后端旧认证链路：移除本地注册/密码登录/验证码重置 API，删除验证码模型与邮件验证码工具，并把鉴权依赖收口为通用 Bearer 模式。
- 调整 `init_database.py` 为全新库场景：初始化时直接创建绑定 SSO subject 的管理员账号，不再依赖本地密码引导。
- 新增基于 Casdoor claims 的新用户角色初始化规则：可通过 `.env` 配置管理员 claim 和匹配值，在首次创建本地用户时决定是否生成为 `admin`。
- 新增 `docs/casdoor-callback-setup.md`，明确 Casdoor Application `Redirect URL`、本站 `CASDOOR_REDIRECT_URI` 与上游 OAuth Provider callback 的区别，避免回调地址配置混淆。
- 调整用户邮箱策略：本地 `users.email` 不再作为唯一标识，SSO 身份继续以 `auth_provider + auth_subject` 为准；自动按邮箱绑定账号时，若命中多个本地账号则拒绝自动绑定。
- 清理前端旧认证残留：删除未使用的本地密码登录封装与 `useAuth` 组合函数，移除重复的注册页实现，并让 `/register` 直接复用现有 SSO 入口页。
- 修复核心链路中的三个真实断点：管理员拒绝审核现在向后端发送 `archived` 状态；为节点详情页补上了直接子分支列表接口 `/api/v1/story/node?parent_id=...`，前端子分支卡片改为使用摘要字段；同时为连续阅读页补上 `/api/v1/story/node/{id}/lineage` 路由兼容，避免前后端接口名不一致导致 404。
- 收口投稿审核反馈：投稿成功后会带 `submitted=1` 回到节点页并显示待审提示；节点详情页会根据 `pending/archived/freeze_interactions/is_ending` 展示状态说明并禁用续写入口；通知页也会显示审核驳回原因。
- 补充 `backend/.env.example`，把数据库、本地 JWT、Casdoor SSO、管理员初始化参数集中成模板；同时将 `CORS_ORIGINS` 改成支持通过环境变量配置，避免部署时只能改代码。
- 调整管理员来源策略：`init_database.py` 不再强制要求手填 `ADMIN_AUTH_SUBJECT` 才能初始化数据库；默认改为由 Casdoor admin claim 在首次 SSO 登录时自动创建/同步本地管理员角色。SSO 登录同步时也会刷新本地 `admin/writer` 角色，但会保留本地 `banned` 封禁状态。
- 为测试环境补充启动方案：后端 `main.py` 支持通过 `BACKEND_PORT` 指定端口，前端 `vite.config.ts` 支持通过 `VITE_PORT` 和 `VITE_API_PROXY_TARGET` 指定测试端口与代理目标；新增 `docs/testing-environment-setup.md` 说明如何用 `8401/5174` 启动并对齐 Casdoor callback。
- 修复前端 SSO 失败时的二次报错：`error-handler.ts` 不再在普通工具函数里调用 `useMessage()`；同时当 `VITE_PORT=5174` 且未显式指定代理目标时，前端开发代理会默认指向 `http://127.0.0.1:8401`，避免测试环境仍误打到旧的 `8057`。
- 新增 `docs/frontend-visual-style-guide.md`，把项目前端视觉统一收口为“黑白 + 锐利 + 极简 + 科幻”的设计指导，约束首页、故事册、树导航台、正文页、创作页、后台页和核心组件的风格边界。
- 将这套视觉系统继续落到故事树和叙事页面：`StoryTreeFlow.vue` 去掉紫色演示感，改为冷白终端式节点和路径；`StoryNodePage.vue`、`StoryWritePage.vue` 收口为统一的阅读/创作终端界面。
- 继续朝可维护的设计系统收口：在 `frontend/src/styles.css` 中新增共享语义类（如 `ui-panel-section`、`ui-metric-card`、`ui-terminal-input`、`ui-status-note`），为后续页面去散落 CSS、提高组件样式复用度做准备。
- 继续把入口页拉回同一套设计系统：首页 `HomePage.vue` 与故事册列表 `BookListPage.vue` 现在统一复用 `styles.css` 中的页面骨架、归档卡片与筛选语义类，减少页面内硬编码色值和重复视觉规则。
- 收口这轮前端验收遗留：修复 `StoryWritePage.vue` 提交成功后仍弹草稿保存确认的问题；将 `StoryNodePage.vue` 的错误 `<nspace>` 标签改回真实的 `n-space`；并让 `BookDetailPage.vue` 的续写/分支按钮与节点详情页共用同一套节点状态约束。
- 将 `BookDetailPage.vue` 右侧节点检视器抽出为 `frontend/src/components/story/StoryTreeInspector.vue`，把书页收回到“拉数据 + 维护选中状态”的页面职责，后续节点预览、路径操作和创作提示可独立迭代。
- 将“节点是否允许继续创作”的判断与阻断提示抽到 `frontend/src/features/story/creation.ts`，让 `BookDetailPage.vue` 与 `StoryNodePage.vue` 共用同一份规则，避免后续节点状态变更时出现页面间行为不一致。
- 将 `StoryNodePage.vue` 的评论提交流程收口到 vue-query cache：评论提交和删除后现在通过 `invalidateQueries` 刷新 `node-comments` 与 `story-node`，不再直接改写 `useQuery` 返回值。
- 继续收薄故事树组件：将 `StoryTreeFlow.vue` 中的节点卡模板抽出为 `frontend/src/components/story/StoryTreeFlowNode.vue`，让树图主组件回到“布局、视口、交互事件”的职责边界。
- 开始统一前端数据调用约定：新增 `frontend/src/features/queryKeys.ts` 作为共享 query key 定义，先把故事节点、评论、书籍与通知相关页面/组件接回同一套 key；同时确认评论删除统一使用后端正式接口 `DELETE /interaction/comment/{comment_id}`，移除前端里残留的旧删评协议写法。
- 新增 `docs/frontend-data-layer-guide.md`，把前端数据层的统一模式写成文档，明确 `http.ts`、`features/*/api.ts`、`features/*/queries.ts`、`features/queryKeys.ts` 与页面层的职责边界，并记录当前一致性检查结果与后续收口方向。
- 继续收紧前端数据层：`useBookQuery` 改为使用单本书正式接口而非“拉全量后 find”；`features/story/queries.ts` 与 `features/interaction/queries.ts` 中的删评、点赞和通知已读 mutation 改成更精确的缓存失效策略，减少对整类资源的宽泛刷新。
- 继续把页面层请求回收到 feature 数据层：为故事节点补上子分支、完整分支阅读和节点删除相关 query/mutation hook；`StoryNodePage.vue`、`StoryLineagePage.vue`、`NotificationPage.vue`、`NotificationPanel.vue` 现在统一通过 `features/story/queries.ts` 与 `features/interaction/queries.ts` 组合数据，不再在页面里散写业务请求。
- 继续统一后台管理的数据层：新增 `frontend/src/features/admin/api.ts` 与 `frontend/src/features/admin/queries.ts`，把管理员仪表盘、用户列表/更新收进 admin feature；`AdminDashboardPage.vue`、`AdminPendingNodesPage.vue`、`AdminBooksPage.vue`、`AdminUsersPage.vue` 现在统一复用 feature query/mutation，并改回后端真实存在的 `/admin/stats`、`/admin/users`、`/admin/nodes/pending`、`/admin/nodes/{id}/audit` 等接口。
- 继续收口 feature 边界：评论相关 API/query/mutation 从 `features/story/*` 中移除，只保留在 `features/interaction/*`；待审核节点与审核 mutation 从 `features/story/*` 移到 `features/admin/*`，避免故事资源、互动资源、后台资源继续交叉持有同一职责。
- 继续把页面/组件层收回统一 hook：`CommentForm.vue`、`CommentList.vue`、`BookListPage.vue`、`BookDetailPage.vue`、`StoryWritePage.vue`、`NotificationBell.vue`、`LikeButton.vue` 现在都改为优先组合 `features/story/queries.ts` 或 `features/interaction/queries.ts`，页面和组件层不再重复声明同一套 query/mutation。
- 修复管理员后台按钮“看起来可点但不跳转”的问题：将 `AdminDashboardPage.vue`、`AdminBooksPage.vue`、`AdminPendingNodesPage.vue` 中依赖 `n-button + RouterLink` 的入口改成显式 `router.push(...)`，避免 Naive UI 按钮组合路由组件时出现无响应。
- 修复 `BookDetailPage`/`StoryTreeFlow` 中的 `useVueFlow is not a function`：确认当前项目安装的是错误的旧包 `vue-flow@0.3.0`，并非现代 `@vue-flow/core`；将故事树画布改为项目内可控的拖拽/缩放实现，移除前端对该错误依赖和本地伪类型声明的使用。
- 全面清理前端中不稳定的 `n-button + RouterLink` 组合：统一改为显式 `router.push(...)`，覆盖首页、故事册列表、书页、节点页、分支页、通知页、个人中心、异常页、发现栏和树检视器，避免按钮表现依赖未定义的组件透传行为。
- 合并前端中语义重复的“沿此续写 / 创建分支”入口，统一为“创建后续节点”，同步收口书页、节点页、分支阅读页、检视器和写作页文案，避免同一子节点创建行为被误导成两种不同操作。
- 暂时下线书页与节点检视器中的“阅读本条分支/查看当前分支”入口，当前统一以节点树视图为主工作区，避免在独立分支阅读页和树视图之间分散主链路。
