# 后端审阅总览 — 「指标说谎」与前后端协同（2026-06-02）

本轮由 3 个并行审阅 agent 完成，聚焦"指标说谎"与前后端契约。配套文档：

| 文档 | 内容 |
|---|---|
| [`../backend/api.md`](../backend/api.md) | **后端 API 完整参考**（源码核对版，37 个端点） |
| [`02-frontend-needs-and-metric-lying.md`](02-frontend-needs-and-metric-lying.md) | 前端每页消费的接口 + 显示指标的真实/说谎/缺失分类 |
| [`03-backend-core-correctness.md`](03-backend-core-correctness.md) | 后端核心正确性（计数完整性、trending、聚合、软删一致性） |

---

> **执行进展（2026-06-02）**：A+C+B 全部落地，见 `../changelog.md`。
> - ✅ A 类零成本：4 处前端改用已存在真值。
> - ✅ C 类计数完整性：6 处计数原子化 + `children_count` 归档回收 + `nodes_count` 口径对齐 + `/admin/stats` 排除封禁 + 对账脚本。
> - ✅ B 类总数契约：discovery×4 / notifications / books 走 `X-Total-Count`（非破坏），前端 `getList` 消费；首页/搜索/通知/书列表的说谎点已修。
> - ⬜ 仍开放：trending 时间衰减真热度公式（§2.6）、admin 列表"按筛选命中数"（后端 header 已可扩展，前端 hero 暂用全站 stats）、UNLISTED 可见性维度。

## 一句话结论

**"指标说谎"不是某个页面的 bug，而是一个契约缺口叠加一个数据完整性缺口：**
1. **契约层**：后端**所有列表端点都返回裸 `List[X]`，不带 `total`**。前端只能把 `limit` 截断后的 `array.length` 当成总数显示。
2. **完整性层**：少数真实总数（`likes_count/comments_count/children_count`、`/admin/stats`）本身是**非原子累加**且**软删不一致**，长期会漂移——即"有总数的地方，总数也可能不准"。

好消息：**一半的说谎点是零成本修复**——真实总数其实已经躺在现有响应里，前端只是没用。

---

## 说谎点分级（来自 02 + 03 交叉核对）

### A 类 — 零成本修复（真实总数已存在，前端改用即可）

| 说谎点 | 现状 | 真实来源（已存在） |
|---|---|---|
| ProfilePage hero「Nodes」`ProfilePage.vue:172` | `submittedNodes?.length`（limit:5） | `user.nodes_count`（`/auth/me` 已返回） |
| StoryNodePage「子分支（N）」`StoryNodePage.vue:336,373` | `children.length`（limit:5） | `node.children_count`（节点详情已返回） |
| AdminPendingNodes hero 待审/已归档/结果数 `:48-50` | filter 一个 limit:80 的截断数组 | `/admin/stats` 的 `nodes.pending/archived/total` |
| AdminUsers hero「Visible Users」`:57` | `users.length`（默认 limit） | `/admin/stats` 的 `users.total` |

> 这 4 处只动前端，不动后端。AdminPendingNodes 当前甚至与诚实的 Dashboard 数字自相矛盾。

### B 类 — 需后端补「总数」能力

| 说谎/缺失点 | 需要 |
|---|---|
| HomePage hero 三栏 telemetry + 搜索「MATCHED N」`HomePage.vue:112-114,525` | 各 feed / 搜索的真实总数（当前无任何 count 来源） |
| NotificationPage hero「Total」+「N 条」`NotificationPage.vue:50,178` | 通知总数（仅 unread 有专门端点，是可抄的范本） |
| BookListPage hero「Books」`:71` | 若 `/story/books` 有默认 limit 则说谎 → 需 books 总数 |

### C 类 — 让"有总数的地方也不准"的后端缺陷（来自 03）

- **【高】计数非原子**：`likes_count/comments_count/children_count` 全是 read-modify-write（`interactions.py:43/47/92`、`interaction.py:271`、`story.py:593`、`story_nodes.py:90`），并发丢更新、单调漂移、无对账。followups §1.1 只点了前 3 处。
- **【高】trending 名不副实**（`discovery.py:121-130`）：时间窗只筛 `created_at`，却按历史累计 `likes_count` 排序，且冷场静默退回 all-time，UI 无标识。
- **【中】同一用户两套数字**：`/auth/me` 的 `nodes_count` 含全状态（`auth.py:70-82`），`/users/{id}` 只含 published（`users.py:43/53`）——"我的主页"和"别人看我"对不上。
- **【中】comments_count 含软删脏数据**（`interaction.py:271` 删评 -1 同样 race；列表 `:69` 正确过滤软删）→ 顶部数字与实际列出条数不一致。
- **【中】children_count 归档不回收**（`story_nodes.py:147`）→ 比树里可见子节点多。
- **【中】/admin/stats 活跃用户虚高**（`admin.py:241/265`）：未排除 banned / `banned_until>now`。
- **【中】NodeVisibility 是死维度**：读路径只过滤 status，`UNLISTED` 设计完全未实现。

正面：可见性 status 过滤跨端点一致；`/tree`、`/node/path` 无 N+1；`/admin/stats` 单表 count 无双计。

---

## 关键设计决策：如何暴露「总数」（B 类的前提）

这是本轮优化的分叉点，影响工作量与契约稳定性：

- **方案 1：响应信封** `{ items: [...], total, skip, limit }` 包裹所有列表
  - 优点：标准、显式、强类型。缺点：**破坏性**，要改全部 14 个端点 + 全部前端 query hook + 类型。
- **方案 2：`X-Total-Count` 响应头**（保持 body 仍是裸 list）
  - 优点：**非破坏**，端点逐个加、前端逐个读，可灰度。缺点：header 易被忽略、TanStack Query 需取 header。
- **方案 3：targeted count 端点 / 复用聚合**（只在确有需要处加 `/discovery/*/count` 或扩展 `/admin/stats`、`/story/books/count`）
  - 优点：最小改动、精准。缺点：count 与 list 两次往返、易再次发散。

**推荐：A 类（零成本）先做** → 再用**方案 2（X-Total-Count）**统一补 B 类（非破坏、可灰度）→ C 类计数完整性单独成批（原子化 `UPDATE ... SET x = x ± 1` + 一次性对账脚本）。

---

## 建议落地顺序

1. **A 类零成本**（仅前端）：4 处改用已存在的真实字段/`stats`。立竿见影、零后端风险。
2. **C-高 计数原子化**：把 6 处 `count += 1` 改为 SQL 原子自增/自减（带防负），加一个对账校准脚本。这是"热榜可信"的前提。
3. **语义对齐**：统一 `nodes_count` 口径；`comments_count` 改为 `count(deleted_at IS NULL)` 真值或在删评时一致维护；children_count 归档回收；`/admin/stats` 活跃用户排除封禁。
4. **B 类 总数能力**：按方案 2 给列表端点加 `X-Total-Count`，前端逐页改用。
5. **trending 重做**（可选/远期）：按时间窗内增量赞或 HN 衰减公式排序，冷场加标识。

> 动手前按 CLAUDE.md：先用对应 superpowers 技能、维护 `changelog.md`、完成后从 `followups.md` 迁出 §1.1 等。
