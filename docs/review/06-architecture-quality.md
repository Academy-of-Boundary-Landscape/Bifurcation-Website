# 06 - 横切架构 / 工程质量评审

> 评审范围：`frontend/src` 全树的系统性模式，对照 `docs/frontend/data-layer.md`（数据层契约）与 `docs/frontend/visual-style.md`（视觉 token），并对照 `docs/followups.md` 已记待办。
> 评审属性：只读评审，未改动任何源码。

## 概览

总体结论：**数据层契约执行得相当到位，分层干净；但工程脚手架债务较重、缺少基础设施层配置、类型与设计 token 存在重复与漂移、零测试。**

做得好的部分（事实核验）：

- 数据层四层（`http` → `features/*/api` → `features/*/queries` → `queryKeys`）确实落地。`grep` 全树确认：`pages/`、`components/`、`layouts/` 中**没有**任何直接 `get/post/put/patch/del<...>` 业务调用，也**没有**任何页面/组件直接 `import ... from '@/services/http'`（契约第 213-218 行声称的"已清掉页面散写"属实）。
- query key 全部由 `features/queryKeys.ts` 单一来源提供，未发现页面散写字符串 key。`storyNode` / `node-detail` 双 key 的历史问题确已消除。
- 全树 `grep '\bany\b'` 在 `.ts`/`.vue` 中**零命中**；`tsconfig` 经 `@vue/tsconfig` 继承 `strict: true` + `noUncheckedIndexedAccess` + `verbatimModuleSyntax`，TS 严格度高。`vue-tsc --build` 跑通无报错。
- 缓存失效粒度普遍精确（点赞按 `bookId` 精确失效、删评必带 `nodeId`），与契约第 226-238 行一致。

主要问题集中在：脚手架/死代码清理、缺失的全局基础设施（QueryClient 默认项、全局错误边界、错误处理统一）、类型重复与漂移、设计 token 双轨、构建配置缺失、零测试。

---

## 发现

### 死代码 / 遗留脚手架

**【高】`stores/counter.ts` 整文件为 Vite 模板残留**
`frontend/src/stores/counter.ts:1-13`。`useCounterStore` 全树零引用（`grep` 仅命中无关的 `write__counter` CSS 类）。
建议：删除。

**【高】`stores/ui.ts` 整个 store 未被使用**
`frontend/src/stores/ui.ts:4-39`。`useUIStore` / `globalLoading` / `toggleDarkMode` / `sidebarOpen` 全树零外部引用。`darkMode` 注释写"预留扩展"，但主题实际硬编码在 `App.vue`，该 store 是死代码。
建议：删除整个 store；若日后要做亮/暗切换再按需重建，避免"预留"长期烂在仓库里。

**【高】`utils/validation.ts` 整文件未被使用**
`frontend/src/utils/validation.ts:1-117`。`validateStoryNode` / `isValidEmail` / `validateUserRegistration` / `ValidationUtils` 全树零外部引用。注意其中 `isValidPassword`、`validateUserRegistration` 面向"邮箱+密码注册"，但本项目登录是 SSO（`auth.ts` 全走 Casdoor），这些校验逻辑与实际产品形态不符。
建议：删除（或仅保留 `validateStoryNode` 的字数规则并真正接到 `NodeEditor`，详见下条）。

**【中】`composables/usePageTitle.ts` 与 `components/common/PageTitle.vue` 均未被使用**
`frontend/src/composables/usePageTitle.ts:4`、`frontend/src/components/common/PageTitle.vue`。`usePageTitle` 全树零引用；`PageTitle` 组件仅自身文件命中。页面标题目前无统一方案。
建议：二选一——要么删除，要么真正接入（更好的做法是在 `router/index.ts` 用 `meta.title` + 一个全局 `afterEach` 守卫统一设置 `document.title`，比逐页 composable 更可靠）。

**【中】`components/common/` 下多数组件是未使用的脚手架**
`ConfirmDialog.vue` / `EmptyState.vue` / `ErrorBlock.vue` / `LoadingBlock.vue` / `AppFooter.vue` 全树零外部引用（`grep -rln` 仅命中自身），仅 `UserAvatar.vue` 被用 1 处。
建议：删除未用组件；若 `LoadingBlock`/`ErrorBlock`/`EmptyState` 是想统一加载/错误/空态展示，应实际推广到各页面（目前各页面各自手写 `n-spin`/`message.error`），否则就是噪声。

**【中】`utils/storage.ts` 中的 `StorageManager` 类与 `setUser/getUser/setToken/...` 全部未用**
`frontend/src/utils/storage.ts:4-81`。仅便捷函数 `getStorage/setStorage/removeStorage` 被 `StoryWritePage.vue` 使用；`StorageManager` 类（含 `setDraft/getDraft/clearAll/setUser` 等）以及 `auth.ts` 直接用裸 `localStorage`（`auth.ts:34,46,129...`）绕过了它，导致 token/user 存储有两套并存的约定（`StorageManager` 用前缀 `bifurcation_`，`auth.ts` 用裸 `auth_access_token`）。
建议：删除 `StorageManager` 类，只保留三个便捷函数；或反过来让 `auth.ts` 也走统一封装。当前是"有封装但没人用"的最差状态。

**【中】`frontend-temp/` 目录是早期脚手架，仍被 git 跟踪**
`frontend-temp/FRONTEND_WORKLIST.md`、`frontend-temp/api_documentation.md`（`git ls-files` 确认在版本控制内）。
建议：内容已并入正式 `docs/` 的话直接删除，避免文档双份。

**【低】仓库根目录存在与 `frontend/` 完全相同的未跟踪副本**
工作目录下 `/src`、`/uno.config.ts`、`/vite.config.ts`、`/package.json` 等与 `frontend/` 下同名文件并存；`diff -rq src frontend/src` 返回**完全一致**，且 `git ls-files` 确认这些根级副本**未被跟踪**。疑似一次误 `cp` 或第二个 checkout。虽不影响构建（真实工程在 `frontend/`），但对任何人都是强误导项。
建议：删除根级这批未跟踪副本（或在 `.gitignore` 明确忽略并在 README 说明）。

### 全局基础设施缺失

**【高】`VueQueryPlugin` 未配置任何 `QueryClient` 默认项**
`frontend/src/main.ts:15` 直接 `app.use(VueQueryPlugin)`，没有传入自定义 `QueryClient`。即全局使用 TanStack 默认：`staleTime: 0`（每次挂载都判定 stale）、`retry: 3`（含对 4xx 也重试）、窗口聚焦自动 refetch。对一个以"读多写少 + SSO token 可能 401"为特征的站点，这意味着：401 会被无意义重试 3 次、切回标签页会重新打全部请求。
建议：在 `main.ts` 显式 `new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: (count, err) => 仅对 5xx/网络错误重试, refetchOnWindowFocus: false } } })`，并通过 `VueQueryPlugin` 的 `queryClient` 选项注入。

**【高】没有任何全局错误边界 / 全局 query 错误兜底**
全树 `grep` `onErrorCaptured` / `errorCaptured` / `app.config.errorHandler` / `ErrorBoundary` **零命中**。任何子组件渲染异常或未被 `onError` 捕获的 query 失败都会静默或冒泡到控制台，用户无反馈。
建议：在 `main.ts` 设 `app.config.errorHandler`；在 `QueryClient` 上配 `QueryCache({ onError })` 做统一失败提示；并对关键路由用一个轻量 ErrorBoundary 组件兜底渲染异常。

**【高】错误处理三套并存，且 `error-handler.ts` 用 `window.alert`**
- 各业务页用 Naive 的 `message.error(...)`（`StoryNodePage.vue:66`、`AdminBooksPage.vue:186`、`ProfilePage.vue:112` 等，共 5+ 页），UX 一致且好。
- `utils/error-handler.ts:49-50` 的 `handleError` 走 `window.alert(...)`——阻塞式原生弹窗，与全站视觉/交互完全不搭，仅在 3 个 SSO 文件用（`DefaultLayout.vue:123`、`LoginPage.vue:22`、`AuthCallbackPage.vue:45`）。
- `components/editor/NodeEditor.vue:30,35` 直接裸 `alert('内容不能为空')`。
三种风格（`message` / `error-handler+alert` / 裸 `alert`）并存。
建议：统一到 Naive `message`/`dialog`。`error-handler.ts` 的 `resolveErrorMessage`（解析 FastAPI `detail` / 422 `detail[]`）逻辑很有价值，应保留**消息解析**部分，但把 `notifyError` 从 `window.alert` 换成全局 message API（可通过 `naive-ui` 的 `createDiscreteApi` 在非组件环境调用）。`NodeEditor` 的 `alert` 改用同一通道。

### 类型层：重复定义与漂移风险

**【高】`ApiResponse` / `PaginatedResponse` / `ApiErrorResponse` 在 `api.ts` 与 `models.ts` 各定义一份**
`frontend/src/types/api.ts:2,8,31` 与 `frontend/src/types/models.ts:225,231,240`。同名类型双份定义，且 `ApiErrorResponse` 两份**结构还不完全一致**（`api.ts` 用 `ErrorResponse | ValidationErrorResponse` 联合，`models.ts:240` 用内联匿名联合）。`error-handler.ts` import 的是 `@/types/api`，但 `models.ts` 也对外导出同名类型——后续谁 import 错就会拿到不同形状。
建议：删除 `models.ts:224-244`（含注释 `按照 cline.md 规范...`）这批与 `api.ts` 重复的定义，单一来源放 `api.ts`。`MessageResponse` 同理（`api.ts:50` 已有，后端侧也有重复——见 `followups.md 1.2`）。

**【中】前后端类型纯手维护，无 codegen，漂移风险已显现**
全树 + `package.json` `grep` `openapi`/`orval`/`codegen`/`swagger` **零命中**，`types/api.ts`、`types/models.ts` 全靠手写跟后端 schema 对齐。`frontend-temp/api_documentation.md` 是手抄 API 文档，进一步说明靠人肉同步。
建议：后端是 FastAPI，自带 `/openapi.json`。引入 `openapi-typescript`（仅 devDependency，生成 `types/api.gen.ts`）作为单一真相源，手写类型只保留前端专用扩展（如 `DiscoveryRailItem`）。这是降低长期漂移成本最高杠杆的一项。

**【中】大量 `types/api.ts` 类型为死定义**
`grep` 确认零外部引用的导出类型至少有：`UserStatsResponse`、`StoryBookNodeStats`、`NodeTreeStats`、`AdminNodeStatsResponse`、`UserNodeStatsResponse`(仅 1 处)、`StoryBookNodesCountResponse`、`NodePathResponse`、`StoryTreeResponse`、`StoryBookStatsResponse`、`UserNotificationsSummary`、`NotificationCountResponse`、`UploadResponse`、`PaginatedResponse`、`TokenResponse`、`StoryNodeWithBookTitle`。多数是早期为臆想接口预留的统计响应类型，与契约第 186 行"不再调用前端臆造的统计接口"对应——接口删了但类型残留。
建议：随 codegen 引入一并清理；在 `tsconfig.app.json` 打开 `noUnusedLocals` 帮助持续发现。

### 设计 token 纪律

**【高】`uno.config.ts` 的 `accent: '#8b5cf6'`（紫色）违反视觉规范，且确有页面在用**
`frontend/uno.config.ts:53` 定义 `accent: '#8b5cf6'`，注释"紫色强调色"。`visual-style.md:353` 明确列"紫色泛滥的通用 AI 科技风"为**应主动避免**方向。且非死配置：`StoryLineagePage.vue:66,86`、`StoryBranchPath.vue:38,47` 直接写死 `text-#8b5cf6` / `ring-#8b5cf6`（绕过 token，直接 hex）。
建议：删除 `accent` 紫色或改为规范允许的"偏冷白 / 低饱和蓝白"选中色；同步把那 4 处硬编码 `#8b5cf6` 改为引用 token。

**【中】UnoCSS token 与 `App.vue` Naive 主题色盘双轨且不一致**
`uno.config.ts` 定义 `card: '#1a1a1a'`、`secondary: '#0f0f0f'`、`border: '#2a2a2a'`；而 `App.vue:16-20` 的 Naive `themeOverrides` 用 `cardColor: '#101010'`、`borderColor: rgba(255,255,255,0.12)`。两套配色体系并行，UnoCSS 类画的卡片和 Naive 组件画的卡片底色不一致（`#1a1a1a` vs `#101010`）。
建议：以一套 CSS 变量为单一真相源（`visual-style.md:362-371` 的"先定义全局设计 token"建议正是此意），让 uno shortcuts 与 Naive themeOverrides 都引用同一组变量。

**【中】`.vue` 中硬编码 hex 颜色 100+ 处**
`grep -E '#[0-9a-fA-F]{6}'` 在 `.vue` 命中 100+ 行。`uno.config.ts` 已经提供 `card-base`/`text-primary`/`bg-card` 等 shortcuts（被使用约 94 处），但仍有大量散落的 `bg-#1a1a1a`、`border-#3a3a3a`、`#8b5cf6` 等裸值（含 `#3a3a3a` 这种连 token 都没有的灰阶）。
建议：把常用灰阶/状态色收敛进 `uno.config.ts` 的 `theme.colors` 或 shortcuts，逐步替换裸 hex。

### Store / 路由 / 构建

**【中】`services/http.ts` 残留未使用 import `useMessage`**
`frontend/src/services/http.ts:3` `import { useMessage } from 'naive-ui'` 全文件未使用。`verbatimModuleSyntax` 下这是真实多余 import（也佐证响应拦截器本应做统一提示却没做，呼应上面"全局错误兜底缺失"）。
建议：删除该 import；并考虑在响应拦截器对 5xx/网络错误做统一 message 提示。

**【中】401 处理只清状态、不触发跳转**
`http.ts:36-39` 拦截 401 仅 `authStore.logout()`，无路由跳转，依赖"下一次导航时守卫拦截"。若用户停在受保护页面（如创作页）且 token 过期，页面会保持在原地、后续请求持续 401（且因 QueryClient 默认 `retry:3` 还会各重试 3 次），用户无明显反馈。
建议：401 后除 logout 外，对带 `requiresAuth` 的当前路由主动 `router.replace({name:'login', query:{redirect}})`；并把 401 排除出 retry。

**【中】`app.use(naive)` 全量注册整个 Naive UI，是 1.5MB chunk 的主因**
`main.ts:16` `app.use(naive)` 把**整个** Naive UI 组件库注册为全局组件并打进主 chunk；与此同时各组件又分别 `import { NCard, ... } from 'naive-ui'`（47 处按需 import）。两者重复，全量注册让 tree-shaking 失效。这正是 `followups.md 4.1` 记录的 `index-*.js` 1.5MB（gzip 426KB）超 Vite 500KB 警告的根因，而 followups 只提了 `manualChunks`，没点出全量注册问题。
建议：删除 `main.ts` 的 `import naive` + `app.use(naive)`，全面改为各组件按需 import（已有 47 处在用）；`MessageProvider`/`DialogProvider` 这类需要 provider 的单独显式引入即可。配合 `vite.config.ts` 加 `build.rollupOptions.output.manualChunks` 拆分 vendor，双管齐下。

**【中】`vite.config.ts` 缺少 `build` 配置（manualChunks / sourcemap / chunkSizeWarningLimit）**
`frontend/vite.config.ts` 无任何 `build` 段。生产无 sourcemap（线上排错难）、无 vendor 分包、无 chunk 体积调优。
建议：加 `build.sourcemap`（至少 `hidden`）、`build.rollupOptions.output.manualChunks`（拆 `naive-ui`/`@tanstack`/`vue-router`/`date-fns`）。

**【低】路由守卫无 `requiresWriter` / 被封禁用户拦截**
`router/index.ts:111-133` 守卫仅处理 `requiresAuth`/`guestOnly`/`requiresAdmin`。`auth.ts` 已暴露 `isWriter`/`isBanned`，但路由层没有对 `banned` 角色访问创作页做拦截（仅靠后端 + 节点级 `creation.ts` 判断）。
建议：视产品需求决定是否在守卫层加 banned 拦截，避免被封用户进创作页后才在提交时被拒。

**【低】`env.d.ts` 未声明 `ImportMetaEnv`（自定义 VITE_ 变量无类型）**
`frontend/env.d.ts` 仅 `/// <reference types="vite/client" />`。`vite.config.ts` 读取了 `VITE_PORT`、`VITE_API_PROXY_TARGET`，但前端代码若要用自定义 `import.meta.env.VITE_*` 没有类型提示/约束。当前前端只用了内置 `BASE_URL`/`DEV`，影响小。
建议：补 `interface ImportMetaEnv` 声明，为将来自定义环境变量留类型护栏。

### 其它一致性

**【中】`useNodeCommentsQuery` 已是死导出，且与无限版共用 key 前缀**
`features/interaction/queries.ts:39` 的 `useNodeCommentsQuery` 全树零页面引用（`StoryNodePage`、`CommentList` 都用 `useInfiniteNodeCommentsQuery`）。更要注意：普通版 key 是 `nodeComments(nodeId, params)`、无限版是 `nodeComments(nodeId)`（无 params），二者**共享 `['node-comments', nodeId]` 前缀但缓存数据形状不同**（扁平数组 vs `{pages,pageParams}`）。目前因普通版没人用而未爆雷，但同一 key 命名空间下混放两种形状是隐患。
建议：删除死的 `useNodeCommentsQuery`；若保留，给无限查询单独 key（如 `nodeCommentsInfinite`）。

**【低】`features/story/queries.ts` 与 `features/interaction/queries.ts` 评论能力的历史重复已收口，但 followups 第 2 条建议仍标注待办**
契约第 167-171 行称评论 hook 已只留在 `interaction`，本轮 `grep` 核实 `story/queries.ts` 确实不再含评论 hook，契约属实，data-layer.md 第 245 行的"视情况收掉重复"已基本完成，可从后续建议中划掉。

**【低】`data-layer.md` 关于 `ProfilePage` 仍页面直写的描述已过期**
契约第 224 行称"明显剩余的页面级直写数据入口主要是 `ProfilePage.vue`"。实测 `ProfilePage.vue:8` 已改用 `@/features/user/queries`（`useMyProfileQuery` 等），不再直写。文档应更新。

**【高】整个前端零测试、无测试框架**
`find` 无任何 `*.test.ts`/`*.spec.ts`/`__tests__`；`package.json` 无 `vitest`/`@testing-library`/`playwright`。`queryKeys`、`error-handler`（FastAPI detail/422 解析逻辑）、`creation.ts`（创作准入纯函数）、`date.ts` 这些都是**纯逻辑、易测、回归价值高**的单元。
建议：引入 Vitest，先给 `error-handler.resolveErrorMessage`、`creation.canCreateFromStoryNode/getStoryNodeCreationBlockedReason`、`queryKeys` 写单测；关键链路（创作提交、点赞失效）可加组件测试。

### 已记待办（followups.md）状态确认

- `1.4` `scanLatestDraft` 扫全表 + `1.5` 草稿只在 mount 扫描：仍未修，`HomePage.vue:40-44` 确实在 mount 遍历 `localStorage`，无 draft index、无 `useDraftStore`。**未修。**
- `1.6` `StoryWritePage` sticky `top:64px` magic number：**未修。**
- `4.1` chunk size 1.5MB：**未修**（且根因比 followups 描述更深，见上面"全量注册 Naive"一条）。
- `4.2` alembic 未接入：属后端，本评审不展开。

---

## 优先级建议（前 5）

1. **【全局基础设施补齐】** 在 `main.ts` 显式构造 `QueryClient`（`staleTime`、对 4xx 不 retry、关 `refetchOnWindowFocus`）+ 配 `app.config.errorHandler` + `QueryCache.onError` 全局失败兜底。当前缺省项让缓存策略、错误反馈都处于"裸默认"状态，是最影响线上稳定性的一项。（`main.ts:15`）

2. **【错误处理与 alert 统一】** 把 `error-handler.ts` 的 `window.alert`、`NodeEditor.vue` 的裸 `alert` 全部并入 Naive `message`/`dialog`，保留 `resolveErrorMessage` 的 FastAPI detail/422 解析逻辑。消除三套并存的错误反馈风格。（`error-handler.ts:49`、`NodeEditor.vue:30,35`）

3. **【Bundle 瘦身】** 删除 `main.ts` 的 `app.use(naive)` 全量注册（已有 47 处按需 import），并在 `vite.config.ts` 加 `manualChunks` + `sourcemap`。这是 1.5MB chunk 的真正根因，比 followups 4.1 的方案更彻底。（`main.ts:16`、`vite.config.ts`）

4. **【死代码 / 脚手架大扫除】** 删除 `counter.ts`、`ui.ts`、`validation.ts`、未用的 `common/*` 组件、`usePageTitle` + `PageTitle`、`StorageManager` 类、`http.ts` 多余 import、`models.ts` 重复类型、十余个死类型、`frontend-temp/`、根级未跟踪副本；并在 `tsconfig.app.json` 打开 `noUnusedLocals` 防回潮。降低认知负担与误导。

5. **【类型单一真相源 + 视觉 token 收敛】** 引入 `openapi-typescript` 从 FastAPI `/openapi.json` 生成 API 类型，根治前后端漂移；同时删除 `uno.config.ts` 的紫色 `accent:#8b5cf6`（违反 visual-style）、统一 UnoCSS 与 Naive 两套色盘到一组 CSS 变量。（`uno.config.ts:53`、`App.vue:5-70`、`types/*`）
