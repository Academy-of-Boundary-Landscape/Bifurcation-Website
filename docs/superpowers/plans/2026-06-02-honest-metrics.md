# 诚实指标（Honest Metrics）Implementation Plan

> REQUIRED SUB-SKILL: superpowers:executing-plans。后端用 TDD（venv pytest），前端用 type-check + build。

**Goal:** 消除"指标说谎"：A 前端改用已存在真值；C 后端计数原子化+语义对齐；B 列表端点用 `X-Total-Count` 暴露真实总数，前端读取。

**分支:** `feat/honest-metrics`。**验证:** 后端 `cd backend && venv/bin/python -m pytest -q`（基线 29 pass / 1 已知 mock 失败）；前端 `cd frontend && npx vue-tsc --build --force && npm run build-only`。

**Commit 策略:** 每个 Phase 完成且验证通过后提交；全部完成后交用户决定合并部署。

---

## Phase A — 前端零成本（改用已存在真值）

### Task A1: ProfilePage hero「Nodes」
- File: `frontend/src/pages/user/ProfilePage.vue:172`
- 先确认 `/auth/me` 的 `UserProfileResponse` 含 `nodes_count`（`git grep nodes_count backend/app/schemas/user.py backend/app/api/v1/auth.py`）。
- 改 `{{ submittedNodes?.length || 0 }}` → `{{ user?.nodes_count ?? 0 }}`。

### Task A2: StoryNodePage「子分支（N）」
- File: `frontend/src/pages/story/StoryNodePage.vue`（标题计数 ~:336/:373，用 `children.length`）
- 改用 `node?.children_count ?? 0`（节点详情已带）。保留 children 列表本身仍只展示 limit:5（列表是预览，计数用真值）。

### Task A3: AdminPendingNodes hero
- File: `frontend/src/pages/admin/AdminPendingNodesPage.vue:47-50`
- 引入 `useAdminStatsQuery`（`features/admin/queries.ts` 已有），hero 三格改用 `stats.nodes.total/pending/archived`；保留列表本身。把「当前结果」语义改为「全部节点」或新增"当前筛选结果（已加载 N）"明确标注。

### Task A4: AdminUsers hero「Visible Users」
- File: `frontend/src/pages/admin/AdminUsersPage.vue:57`
- 引入 `useAdminStatsQuery`，改用 `stats.users.total`。

**Verify A:** `cd frontend && npx vue-tsc --build --force && npm run build-only` → PASS。Commit。

---

## Phase C — 后端计数完整性（TDD）

### Task C1: 计数原子化（核心）
- Files: `backend/app/services/interactions.py`（toggle like ±1 ~43/47、create comment +1 ~92）、`backend/app/api/v1/interaction.py:271`（删评 -1）、`backend/app/api/v1/story.py:593`（删节点→父 children_count -1）、`backend/app/services/story_nodes.py:90`（建节点→父 children_count +1）。
- 模式：把 `obj.x += 1; commit` 改为
  `await db.execute(update(M).where(M.id==id).values(x=M.x + 1))`；
  减法防负：`values(x=func.max(M.x - 1, 0))`（SQLite/PG 均支持 `max`）。
  commit 后若需返回该值：`await db.refresh(obj, ["x"])` 或重新 `select`。
- TDD：在 `tests/test_sqlite_integration.py` 加/扩展用例：连续点赞→取消→点赞后 `likes_count` 与 `NodeLike` 行数一致；建 N 个子节点后父 `children_count==N`；删 1 个子节点后 `==N-1` 且不为负。
- 步骤：先写失败测试 → 跑 `venv/bin/python -m pytest tests/test_sqlite_integration.py -q` 看失败 → 改实现 → 跑通。

### Task C2: nodes_count 语义对齐
- Files: `backend/app/api/v1/auth.py:70-82`（/me 含全状态）vs `backend/app/api/v1/users.py:43/53`（仅 published）。
- 决策：两端口径一致——`/auth/me` 的 `nodes_count` 也改为仅 `PUBLISHED`，与公开主页一致（"Nodes"=已发布贡献）。
- 测试：扩展 admin/story 集成测试断言 /me 与 /users/{id} 对同一用户返回相同 nodes_count。

### Task C3: comments_count 真值一致
- `backend/app/api/v1/interaction.py:271` 删评 -1（C1 已原子化）。确保列表 `:69` 过滤 `deleted_at IS NULL`（已正确）。对账脚本（C6）兜底历史漂移。

### Task C4: children_count 归档回收
- File: `backend/app/services/story_nodes.py`（audit/archive 路径 ~:147）。
- 节点被 archive 时父 `children_count` 原子 -1（防负）；若有从 archived 恢复为 published 的路径，对应 +1。先读代码确认 audit 状态流转，再对称处理。
- 测试：建父+子（published）→ archive 子 → 父 children_count -1。

### Task C5: /admin/stats 活跃用户排除封禁 + 暴露 banned
- File: `backend/app/api/v1/admin.py:241-265`。
- active 过滤加 `User.role != BANNED AND (banned_until IS NULL OR banned_until <= now)`；响应加 `users.banned`；`inactive` 重新基于真实口径。
- 同步前端 `AdminDashboardPage.vue` + `types/models.ts` 的 `AdminDashboardStats.users` 加 `banned`。
- 测试：建 active/inactive/banned 用户各若干，断言 stats 分类正确。

### Task C6: 对账脚本
- Create `backend/scripts/recount.py`：从源表重算所有节点 `likes_count=count(NodeLike)`、`comments_count=count(StoryComment WHERE deleted_at IS NULL)`、`children_count=count(子节点 WHERE 未删 且 非 archived)`，批量 UPDATE。可重复运行、打印修正条数。
- 不强制现在跑（dev.db），但提供给生产一次性校准。

**Verify C:** `cd backend && venv/bin/python -m pytest -q` → 仅保留基线那 1 个已知 mock 失败，无新增失败。Commit。

---

## Phase B — X-Total-Count（后端 + 前端）

### Task B1: 后端列表端点加 X-Total-Count
- CORS：`backend/app/main.py` 的 CORSMiddleware 加 `expose_headers=["X-Total-Count"]`（否则浏览器读不到）。先确认现有 CORS 配置。
- Helper：在各 list 端点加 `response: Response` 参数，执行与 list 相同 filters 的 `total = await db.scalar(select(func.count()).select_from(M).where(*filters))`，`response.headers["X-Total-Count"] = str(total)`。
- 覆盖端点（按前端需求优先级）：`discovery` featured/feed/trending/search（`discovery.py`）、`interaction` notifications（`interaction.py:120`）、`story` books（`story.py:166`）、children（`:378`）、user nodes（`:455`）、`admin` nodes（`admin.py:38`）/users（`:194`）、comments（`interaction.py:60`）。
- 测试：对 books / notifications / discovery search 各断言响应头 `X-Total-Count` 等于真实总数（建 N 条、limit<N、校验 header==N）。

### Task B2: 前端读取 total
- `frontend/src/services/http.ts`：新增 `getList<T>(url, config?): Promise<{ items: T[]; total: number }>`，读取 `res.headers['x-total-count']`（缺失则回退 `items.length`）。不破坏现有 `get`。
- 在需要总数的 feature 查询改用 `getList` 并通过 `select`/返回结构暴露 `total`：discovery（featured/latest/trending/search）、interaction notifications、story books。
- 修说谎/缺失点：
  - `HomePage.vue` hero 三栏 telemetry + 搜索「MATCHED N」→ 用各 feed 的 total。
  - `NotificationPage.vue:50,178` Total → 用 notifications total。
  - `BookListPage.vue:71` Books → 用 books total。

**Verify B:** 后端 pytest 通过；前端 `npx vue-tsc --build --force && npm run build-only` 通过。Commit。

---

## Phase D — 收尾
- `cd backend && venv/bin/python -m pytest -q`；`cd frontend && npm run build`。
- 更新 `docs/changelog.md`、把 `docs/followups.md` §1.1 迁出、`docs/backend-review/00-overview.md` 标记进展。
- 交用户：汇报 + git status，确认是否合并部署。

## Self-Review
- A→Task A1-4；C→C1-6；B→B1-2；覆盖 00-overview 的 A/B/C 类。
- 无占位符：每步有文件:行号与命令。原子化用 `func.max(x-1,0)` 统一防负。
- 风险：B 改动面大且影响契约——X-Total-Count 为非破坏增量，逐端点/逐查询推进，type-check+pytest 双门槛。
