# 前端代码清洗 — 设计 spec（2026-06-02）

## 目标

让前端项目结构更清晰、功能更简洁：删除已验证零引用的死代码、清理仓库历史噪声、顺手修复已发现的破损/不一致。**不做**整页风格重做、活跃功能精简、全局健壮性/bundle/测试（属后续梯队）。

来源：`docs/review/00-overview.md` 主题 A（死代码）+ 主题 F（破损功能）+ 主题 G（一致性）。所有"死代码"结论均经本人 `grep` 二次验证，并已纠正审阅的两处误报。

## 验证纠正记录

- `components/common/UserAvatar.vue` — 审阅误判为死代码，实测被 `ProfilePage.vue` 等 3 处引用 → **保留**。
- "仓库根存在与 frontend/ 一致的未跟踪副本" — 审阅误报，`git status` 干净，无此副本 → **不处理**。
- `PageTitle` 的"1 处引用"系 `usePageTitle` 函数名子串误匹配，二者均真死 → 删。

## 工作方式

- 分支：`chore/frontend-cleanup`（保持 main 干净）。
- 每个阶段完成后 `npm run type-check` 必须通过。
- 维护 `docs/changelog.md`；完成后从 `docs/followups.md` 迁出对应项（1.4/1.5/1.6 视情况）。
- 全部通过后交用户决定是否提交/合并。

## 范围清单

### A. 整文件删除（已验证零引用，16 个）

`components/common/`：ConfirmDialog.vue、EmptyState.vue、ErrorBlock.vue、LoadingBlock.vue、PageTitle.vue、AppFooter.vue
（保留 UserAvatar.vue）

`components/editor/`：NodeEditor.vue、NodeEditorToolbar.vue、NodePreview.vue、BranchTypeSelector.vue、DraftGuard.vue

`components/story/`：StoryTreePanel.vue

`stores/`：counter.ts、ui.ts

`utils/`：validation.ts
`composables/`：usePageTitle.ts

### B. 局部删死（保功能）

- `utils/storage.ts`：删 `StorageManager` 类（行 4–83），保留 `getStorage/setStorage/removeStorage`（被 StoryWritePage 使用）。
- `services/http.ts`：删未用 `import { useMessage } from 'naive-ui'`。
- `features/admin/queries.ts` + `api.ts`：删 `usePendingNodesQuery`、`fetchPendingNodes`（无外部引用；页面用的是 `useAdminNodesQuery`）。
- `uno.config.ts`：删 `accent: '#8b5cf6'`（违反 visual-style，零引用）。
- `types/*`：逐个 `grep` 确认后仅删确证零引用的死类型；不确定的不动。

### C. 历史噪声（git 移除）

- `frontend-temp/`（FRONTEND_WORKLIST.md、api_documentation.md）
- 根目录 `cline.md`

### D. 顺手修破损/不一致

- **断裂面包屑**：`StoryNodePage.vue:192` 用 `<story-branch-path>` 却未 import → 引入 `StoryBranchPath`；因正要启用它，顺带把其 emoji/紫色/硬编码色拉回 token 黑白终端风。
- **状态枚举中文化复用**：把 `StoryTreeFlowNode.vue:23-38` 的内联中文映射抽到共享 `utils/storyStatus.ts`（`statusLabel(status)`），在仍渲染英文裸 `status` 的 Inspector / StoryNodePage / StoryLineagePage / StoryCreateConfirmModal 复用。

## 验收标准

- `npm run type-check` 通过，无新增类型错误。
- `git grep` 确认被删符号在全仓无残留引用。
- 前端可正常 `npm run dev` 启动（手动冒烟：首页、故事树、节点页面包屑、创作页、后台）。
- 节点页面包屑正常显示；状态标签在上述页面均为中文。

## 风险与回滚

- 风险：误删仍被使用的符号 → 用编译器（type-check）+ git grep 双重把关。
- 回滚：独立分支，未通过即丢弃分支，零污染 main。
