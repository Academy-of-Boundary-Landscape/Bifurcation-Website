# 前端审阅总览（2026-06-02）

本轮由 6 个并行审阅 agent 完成，覆盖前端全部页面与横切架构。各分册：

| 分册 | 范围 |
|---|---|
| [01](01-home-layout-discovery.md) | 首页 / 全局布局 / 发现导航 |
| [02](02-story-tree-reading.md) | 故事树体验 / 阅读（核心承载页） |
| [03](03-writing-editor.md) | 创作 / 编辑器 / 草稿 |
| [04](04-interaction-auth-user.md) | 互动 / 通知 / 认证 / 用户 |
| [05](05-admin.md) | 后台管理 |
| [06](06-architecture-quality.md) | 横切架构 / 工程质量 |

> 评估基准：`docs/frontend/visual-style.md`、`docs/frontend/data-layer.md`、`docs/frontend/tree-experience.md`、`frontend/uno.config.ts`。已与 `docs/followups.md` 去重，下方多为**新发现**。

> **执行进展（2026-06-02）**：第一梯队已完成清洗，见 `docs/changelog.md` 2026-06-02 与 `docs/superpowers/plans/2026-06-02-frontend-cleanup.md`。
> - ✅ 主题 A（死代码）：20 个文件删除/局部删死，已落地。
> - ✅ 主题 F（断裂面包屑）：`StoryNodePage` 已引入 `StoryBranchPath`；ConfirmDialog/DraftGuard 的 bug 随文件删除一并消除；`zone` UI 仍待定（见下）。
> - 🟡 主题 G（一致性·状态枚举中文化）：已统一到 `utils/storyStatus.ts` 并全站复用；搜索去抖、列表分页、a11y 等其余 G 项**未做**。
> - ⬜ 主题 B/C/D/E/H（风格整页重做、全局健壮性、认证兜底、指标说谎、bundle/类型 codegen/测试）：**本轮未做**，留待后续梯队。

---

## 总体判断

**架构底子好，表层债务重。** 四层数据契约（http → features/api → features/queries → queryKeys）真实落地、`vue-tsc` 跑通、零 `any`、TS strict 全开，核心创作链路（`StoryWritePage`）与故事树导航台（`BookDetailPage`）质量过硬。问题集中在三处：**大量死代码、视觉风格回潮、缺少全局健壮性兜底**。

---

## 跨册共性主题（按影响排序）

### 主题 A — 大量死代码（多册一致命中，最高频）
零引用、可直接删除的存量：
- `components/common/*`（7 个）+ `AppFooter.vue`（01/06）
- `components/editor/*`（5 个，且带 `alert()`/坏 `DraftGuard`）（03/06）
- `components/story/StoryTreePanel.vue`（02）
- `stores/counter.ts`、`stores/ui.ts`、`utils/validation.ts` 整文件、`StorageManager` 类、`composables/usePageTitle.ts`+`PageTitle.vue`、`http.ts` 多余 `useMessage` import、十余个死类型（06）
- `features/admin` 的 `usePendingNodesQuery`/`fetchPendingNodes`（05）
- `frontend-temp/` 仍被 git 跟踪；**仓库根存在与 `frontend/` 完全一致的未跟踪副本**（06）

> 风险：死代码本身还违反风格/带 bug，未来重构容易误用。**建议优先清理，立竿见影且零功能风险。**

### 主题 B — 视觉风格回潮 / 紫色违规（违反 visual-style 硬规则）
- `uno.config.ts:53` `accent:#8b5cf6`——正是风格明令禁止的"AI 紫"（01/06）
- `StoryLineagePage` + `StoryBranchPath`：紫色 `#8b5cf6`、emoji（👍📖❌）、`ring-purple`+`scale` 弹跳、硬编码灰——**本应最沉静的连续阅读页，目前是最花的页**（02/06）
- 设计 token 三轨并存：UnoCSS shortcuts vs `styles.css` vars vs `App.vue` Naive themeOverrides，且 card 颜色不一致（#1a1a1a / #101010）（01/06）
- `.vue` 内硬编码 hex 100+ 处（06）；misc 页用 emoji+裸卡片（04）

### 主题 C — 全局健壮性兜底缺失
- `VueQueryPlugin` 无 QueryClient 默认项 → 裸 `retry:3`（含 4xx）、聚焦重拉、staleTime:0（06）
- 无任何全局错误边界（`errorHandler`/`onErrorCaptured` 零命中）（06）
- 错误处理三套并存：Naive `message` / `error-handler.ts` 的 `window.alert` / 裸 `alert()`（04/06）
- `CommentForm` 提交只有 onSuccess 无 onError，失败静默；删评无确认无错误提示（04）

### 主题 D — 认证链路风险（04 主报，安全相关）
- `stores/auth.ts:36` `JSON.parse(localStorage)` 无 try/catch → 数据损坏即全站白屏
- `http.ts:36` 401 静默 `logout()`，不跳登录、不提示；`isAuthenticated` 仅判 token 存在 → "看似已登录实则全 401"
- 无 token 过期/刷新机制；token 存 localStorage 有 XSS 窃取面
- ✅ 正面：全仓无 `v-html`，用户内容全走插值，无注入面

### 主题 E — "指标说谎"再现（与上一个 commit 修的是同类问题）
- 首页 hero 计数显示被各区 `limit`(4) 截断后的 `.length`，伪装成站点总量（01）
- 后台列表 `limit:80`/默认 50 截断 + 无分页 + 对截断数组 `.length` 当总数（05）

### 主题 F — 破损 / 不可达功能
- `StoryNodePage.vue:192` 用了 `<story-branch-path>` 但**从未 import 也无全局注册** → 正文页面包屑静默渲染空白，读者丢失位置感（02，Critical）
- `ConfirmDialog.vue:9` `title="{{ title }}"` 渲染字面量字符串而非绑定（01）
- `DraftGuard` 的 `onBeforeUnmount` confirm 无法真正取消导航，且 `n-modal` 永不打开（03，属死代码）
- 创作页 `zone` 硬编码 `'short'`，长篇 zone 永远产生不了（03）

### 主题 G — 一致性 / 体验细节
- 状态枚举展示混乱：多处渲染英文裸 `status`，而 `StoryTreeFlowNode` 已有中文映射却没复用（02/05）
- 搜索/筛选输入每次按键即查询、无去抖、IME 合成期也触发（01/05）
- 缺 not-found/error 态：`StoryNodePage`/`BookDetailPage` 只解构 `isLoading`，缺失/403 节点显示空转圈（`BookListPage` 是正确样板）（02）
- 可访问性：移动端 ≤960px 隐藏的链接里藏着唯一的未读角标 → 移动端丢失未读提示；头像无 alt/aria-label；状态仅靠颜色区分（01/05）

### 主题 H — 工程基建缺口
- **零前端测试**，无测试框架（06）
- 类型层重复漂移：`ApiResponse`/`PaginatedResponse`/`ApiErrorResponse` 在 `api.ts` 与 `models.ts` 各一份且结构不一致；前后端类型纯手维护、无 codegen → 建议 `openapi-typescript` 从 FastAPI schema 生成（06）
- Bundle：`main.ts:16` `app.use(naive)` **全量注册整个 Naive UI**（与 47 处按需 import 重复），这才是 followups 4.1 记录的 1.5MB chunk 真正主因；`vite.config.ts` 无 `build`/`manualChunks`/`sourcemap`（06）

---

## 建议落地顺序（综合优先级）

**第一梯队（高收益 / 低风险，先做）**
1. **清死代码**（主题 A）：删 common/editor/StoryTreePanel/counter/ui/validation/StorageManager/usePageTitle 等零引用文件 + 根目录 `frontend/` 副本 + 取消跟踪 `frontend-temp/`。
2. **修破损功能**（主题 F）：`StoryNodePage` 引入/注册 `StoryBranchPath`，修 `ConfirmDialog` 绑定（若保留），明确 `zone` 是否需要 UI。
3. **认证兜底**（主题 D）：`JSON.parse` 包 try/catch；401 跳登录+提示；`isAuthenticated` 校验更可靠。

**第二梯队（结构性，需小计划）**
4. **全局健壮性**（主题 C）：配 QueryClient 默认项（4xx 不重试、合理 staleTime）；统一一套错误反馈通道；补全 mutation 的 onError。
5. **风格收口**（主题 B）：删紫色 token；把 `StoryLineagePage`/`StoryBranchPath` 拉回黑白终端风；收敛三轨设计 token 为单一来源。
6. **修"指标说谎"**（主题 E）：hero/后台计数改为后端真实总量或去掉。

**第三梯队（基建 / 远期）**
7. Naive UI 改纯按需注册（去掉 `app.use(naive)`）+ `manualChunks` → 解决 bundle 体积。
8. 引入 `openapi-typescript` 消除前后端类型漂移与重复定义。
9. 搭前端测试框架（Vitest + Vue Test Utils），先覆盖 auth store / features queries。
10. 补一致性细节：状态枚举中文映射复用、搜索去抖、列表分页、not-found 态、a11y（alt/移动端未读角标/非颜色状态）。

> 动手任何一项前，按 CLAUDE.md：先用对应 superpowers 技能、维护 `changelog.md`、做完从 `followups.md` 迁出。
