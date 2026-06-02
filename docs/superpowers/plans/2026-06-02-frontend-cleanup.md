# 前端代码清洗 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除前端已验证零引用的死代码、清理仓库历史噪声、修复断裂面包屑并统一状态枚举中文化，使结构更清晰、功能更简洁。

**Architecture:** 纯删除/局部清理为主 + 两处小修。验证手段不是单元测试（仓库无前端测试），而是 `npm run type-check`（vue-tsc）通过 + `git grep` 确认被删符号零残留引用。在 `chore/frontend-cleanup` 分支进行。

**Tech Stack:** Vue 3 + TS + Vite + vue-tsc。

**说明（commit 策略）:** 计划含 commit 步骤，但实际执行时按 harness 约定"用户要求才提交"——先完成全部改动并通过验证，最后统一向用户确认是否提交。

---

### Task 1: 删除整文件死代码（16 个，零引用）

**Files (删除):**
- `frontend/src/components/common/{ConfirmDialog,EmptyState,ErrorBlock,LoadingBlock,PageTitle,AppFooter}.vue`
- `frontend/src/components/editor/{NodeEditor,NodeEditorToolbar,NodePreview,BranchTypeSelector,DraftGuard}.vue`
- `frontend/src/components/story/StoryTreePanel.vue`
- `frontend/src/stores/counter.ts`
- `frontend/src/stores/ui.ts`
- `frontend/src/utils/validation.ts`
- `frontend/src/composables/usePageTitle.ts`

**保留:** `frontend/src/components/common/UserAvatar.vue`（在用）。

- [ ] **Step 1: 删文件**

```bash
cd /data/sunyunbo/www/Bifurcation-Website/frontend/src
rm components/common/ConfirmDialog.vue components/common/EmptyState.vue \
   components/common/ErrorBlock.vue components/common/LoadingBlock.vue \
   components/common/PageTitle.vue components/common/AppFooter.vue
rm components/editor/NodeEditor.vue components/editor/NodeEditorToolbar.vue \
   components/editor/NodePreview.vue components/editor/BranchTypeSelector.vue \
   components/editor/DraftGuard.vue
rm components/story/StoryTreePanel.vue
rm stores/counter.ts stores/ui.ts utils/validation.ts composables/usePageTitle.ts
rmdir components/editor 2>/dev/null; rmdir composables 2>/dev/null || true
```

- [ ] **Step 2: 确认零残留引用**

Run:
```bash
cd /data/sunyunbo/www/Bifurcation-Website/frontend
git grep -nE "ConfirmDialog|EmptyState|ErrorBlock|LoadingBlock|PageTitle|AppFooter|NodeEditor|NodeEditorToolbar|NodePreview|BranchTypeSelector|DraftGuard|StoryTreePanel|useCounterStore|stores/counter|useUIStore|stores/ui|utils/validation|usePageTitle" -- 'src/*' || echo "NO RESIDUAL REFS"
```
Expected: `NO RESIDUAL REFS`（`usePageTitle` 子串不应再出现；若出现需排查）。

- [ ] **Step 3: type-check**

Run: `cd /data/sunyunbo/www/Bifurcation-Website/frontend && npm run type-check`
Expected: PASS，无新增错误。

---

### Task 2: 局部删死（保功能）

**Files (Modify):**
- `frontend/src/utils/storage.ts` — 删 `StorageManager` 类，保留三个函数
- `frontend/src/services/http.ts` — 删未用 `useMessage` import
- `frontend/src/features/admin/queries.ts` 与 `api.ts` — 删 `usePendingNodesQuery` / `fetchPendingNodes`
- `frontend/uno.config.ts` — 删 `accent: '#8b5cf6'`
- `frontend/src/types/*` — 仅删 grep 确认零引用的死类型

- [ ] **Step 1: storage.ts 删 StorageManager 类**

Read `frontend/src/utils/storage.ts`，删除 `export class StorageManager { ... }` 整段（约行 4–83），保留 `setStorage/getStorage/removeStorage`。

- [ ] **Step 2: http.ts 删未用 import**

删除 `frontend/src/services/http.ts` 中 `import { useMessage } from 'naive-ui'` 这一行（确认文件内无 `useMessage(` 调用）。

- [ ] **Step 3: admin 删死 hook**

在 `frontend/src/features/admin/queries.ts` 删 `usePendingNodesQuery` 定义；在 `api.ts` 删 `fetchPendingNodes`。删前再确认：
```bash
cd /data/sunyunbo/www/Bifurcation-Website/frontend && git grep -n "usePendingNodesQuery\|fetchPendingNodes" -- 'src/*'
```
仅应出现在 admin 这两个文件内部。

- [ ] **Step 4: uno.config.ts 删紫色 token**

删除 `frontend/uno.config.ts` 中 `accent: '#8b5cf6', // 紫色强调色` 这一行（已确认全 src 无 `accent` 引用）。

- [ ] **Step 5: 死类型清理（验证驱动）**

对 `frontend/src/types/{api,models,discovery}.ts` 中每个 `export interface/type/enum X`，执行：
```bash
cd /data/sunyunbo/www/Bifurcation-Website/frontend && git grep -nw "X" -- 'src/*' | grep -v "types/"
```
若结果为空（仅在 types 内部出现）→ 删除该类型。**有任何外部引用则保留。** 不确定不动。

- [ ] **Step 6: 验证**

Run: `cd /data/sunyunbo/www/Bifurcation-Website/frontend && npm run type-check`
Expected: PASS。

---

### Task 3: 清理仓库历史噪声（git 移除）

**Files (删除):**
- `frontend-temp/`（FRONTEND_WORKLIST.md、api_documentation.md）
- `cline.md`

- [ ] **Step 1: git rm**

```bash
cd /data/sunyunbo/www/Bifurcation-Website
git rm -r frontend-temp/ cline.md
```

- [ ] **Step 2: 确认无文档/代码引用这些路径**

```bash
git grep -n "frontend-temp\|cline.md" -- . ':!docs/superpowers' || echo "NO REFS"
```
Expected: `NO REFS`（若 README/docs 有引用则一并更新）。

---

### Task 4: 修复断裂面包屑 + 风格归位

**Files (Modify):**
- `frontend/src/pages/story/StoryNodePage.vue` — 引入 `StoryBranchPath`
- `frontend/src/components/story/StoryBranchPath.vue` — emoji/紫色/硬编码色 → token 黑白终端风

- [ ] **Step 1: StoryNodePage 引入组件**

在 `frontend/src/pages/story/StoryNodePage.vue` 的 `<script setup>` import 区加：
```ts
import StoryBranchPath from '@/components/story/StoryBranchPath.vue'
```
（模板第 192 行 `<story-branch-path :path="path" />` 已存在，无需改模板。）

- [ ] **Step 2: StoryBranchPath 风格归位**

Read `frontend/src/components/story/StoryBranchPath.vue`。把其中 emoji（如 👍📖❌）移除或换为细线/文本；把硬编码 `#8b5cf6`/`#1a1a1a`/`#666666` 等换为 uno shortcuts（`text-primary/secondary/muted`、`border-base`、`bg-card`）。保持现有 DOM 结构与 `:path` 接口不变。

- [ ] **Step 3: type-check + 视觉冒烟**

Run: `cd /data/sunyunbo/www/Bifurcation-Website/frontend && npm run type-check`
Expected: PASS。`npm run dev` 后打开任一节点页，确认面包屑显示当前路径且为黑白风。

---

### Task 5: 状态枚举中文化共享化

**Files:**
- Create: `frontend/src/utils/storyStatus.ts`
- Modify: `frontend/src/components/story/StoryTreeFlowNode.vue`、`StoryTreeInspector.vue`、`StoryCreateConfirmModal.vue`、`pages/story/StoryNodePage.vue`、`pages/story/StoryLineagePage.vue`（仅替换仍渲染英文裸 status 处）

- [ ] **Step 1: 建共享映射**

Create `frontend/src/utils/storyStatus.ts`:
```ts
import type { StoryNodeStatus } from '@/types/models'

const STORY_STATUS_LABELS: Record<string, string> = {
  published: '已发布',
  pending: '待审核',
  archived: '已归档',
  ending: '已完结',
}

export function storyStatusLabel(status: StoryNodeStatus | string | null | undefined): string {
  if (!status) return '未知'
  return STORY_STATUS_LABELS[status] ?? String(status)
}
```
（先 `git grep -n "StoryNodeStatus" src/types` 确认类型名；若不同则改 import 与签名。）

- [ ] **Step 2: StoryTreeFlowNode 复用**

把 `StoryTreeFlowNode.vue:23-38` 内联的 `statusLabel` computed 改为调用 `storyStatusLabel(props.status)`，删除重复 if 分支。import：`import { storyStatusLabel } from '@/utils/storyStatus'`。

- [ ] **Step 3: 其余页面替换裸英文 status**

逐个文件搜索仍直接渲染 `status`（如 `{{ node.status }}`、`{{ status }}`、`:label="status"` 处）：
```bash
cd /data/sunyunbo/www/Bifurcation-Website/frontend && git grep -nE "\{\{ ?[a-zA-Z.]*status ?\}\}|\.status" -- src/components/story/StoryTreeInspector.vue src/components/story/StoryCreateConfirmModal.vue src/pages/story/StoryNodePage.vue src/pages/story/StoryLineagePage.vue
```
在确实把英文枚举展示给用户的位置，替换为 `storyStatusLabel(...)` 并 import。**仅改展示文本，不改用于逻辑判断的 `status` 比较。**

- [ ] **Step 4: 验证**

Run: `cd /data/sunyunbo/www/Bifurcation-Website/frontend && npm run type-check`
Expected: PASS。`git grep` 确认目标文件无遗漏的英文裸 status 展示。

---

### Task 6: 收尾（changelog / followups / 总验证）

- [ ] **Step 1: 全量 type-check**

Run: `cd /data/sunyunbo/www/Bifurcation-Website/frontend && npm run type-check`
Expected: PASS。

- [ ] **Step 2: dev 冒烟**

Run: `cd /data/sunyunbo/www/Bifurcation-Website/frontend && npm run dev`（后台启动），手动确认首页/故事树/节点页面包屑/创作页/后台无报错；停掉 dev。

- [ ] **Step 3: 更新 docs/changelog.md**

追加本轮清洗条目（删除清单、修复项、原因）。

- [ ] **Step 4: 更新 docs/followups.md**

把已被本轮覆盖的项（如 1.4/1.5 草稿、死代码相关）从 followups 迁出或标注；review/00-overview 主题 A/F 标记为已处理。

- [ ] **Step 5: 提交（待用户确认）**

向用户汇报变更摘要与 `git status`，询问是否提交到 `chore/frontend-cleanup` 及是否合并 main。
```bash
cd /data/sunyunbo/www/Bifurcation-Website && git status && git diff --stat
```

---

## Self-Review

- **Spec coverage:** A→Task1、B→Task2、C→Task3、D(面包屑)→Task4、D(状态中文化)→Task5、验收/收尾→Task6。全覆盖。
- **Placeholder scan:** 类型删除(Task2-5)与裸 status 定位(Task5-3)用的是验证流程+具体命令，非占位符；其余步骤均含具体命令/代码。
- **Type consistency:** `storyStatusLabel` 在 Task5 全程同名；`StoryNodeStatus` 类型名在 Step1 要求先 grep 校验。
