# 后续待办（Follow-ups）

记录已识别但**暂未动手**的优化点。每条都来自实际 audit / code review 结论，按主题分组。

> **更新规则**：动手做某项之前，把对应的 Task 提到 in_progress；做完之后从这份文档移到 changelog.md。

---

## 1. 代码债（来自 review）

### 1.1 计数原子化 ✅ 已完成（2026-06-02）

点赞/评论/子节点共 6 处 read-modify-write 已改为原子 SQL（`x=x±1`，减法用 `case` 防负），并新增对账脚本 `backend/scripts/recount.py`。详见 `changelog.md` 2026-06-02。原文保留为历史背景：原 `interactions.py` 两处 + 删评/删节点/建节点三处都会在并发下丢计数，且 leaderboard/trending 直接吃这些字段。

> 关联仍开放项：§2.6 trending 时间衰减（本轮只修了兜底判定与总数口径，未实现 velocity/HN 公式）。

### 1.2 `MessageResponse` 重复定义

`backend/app/schemas/story.py:12` 和 `backend/app/api/v1/interaction.py:16` 各有一份 `MessageResponse`。建议提到 `app.schemas.common`，单一来源。

### 1.3 `get_node_detail` 风格一致性

`backend/app/api/v1/story.py:418-425` 用 `select+selectinload`，但 `update_story_node` 等同类方法用 `db.get` 先验证再 selectinload。两种方式都对，挑一种统一。

### 1.4 `scanLatestDraft` localStorage 扫全表

`frontend/src/pages/home/HomePage.vue:36-71` 在 mount 时遍历 `localStorage` 所有 key 找 `bifurcation_story_node_draft:*`。当前用户基本看不到性能问题；如果将来 localStorage 写入量大，加一个索引 key（`bifurcation_drafts_index`）维护活跃草稿列表。

### 1.5 草稿扫描只在 mount 跑

同上文件：用户在同一个 SPA session 里写完草稿提交后再回首页，banner 仍然显示已经清掉的那条草稿（直到刷新页面）。
**修法**：把 draft 扫描放进一个 pinia store（`useDraftStore`），写作页提交/清除时调用 `store.refresh()`。

### 1.6 sticky offset 硬编码

`frontend/src/pages/story/StoryWritePage.vue` 的 `top: 64px` 是 magic number，假定顶部 strip 永远 64px 高。若日后 strip 内容变多撑高，左栏 sticky 位置就会错位。
**修法**：用 VueUse 的 `useElementSize` 测真实高度，写到 CSS variable。

---

## 2. 互动功能补全（来自 likes/comments/rankings audit）

### 2.1 Leaderboard / 排行榜页面（前端缺失）

后端 discovery 三个接口已能撑起一个排行榜，但前端没入口。

需要开发：
- 路由：`/leaderboard` 或 `/discover`
- 页面分区：
  - **节点榜**：trending（近 7 日）/ all-time top
  - **作者榜**：按贡献节点数 / 收到点赞总数 / 评论活跃度（需要后端新接口聚合）
  - **故事树榜**：按总互动量降序（同样需要后端）
- 后端要新加：
  - `GET /discovery/authors/top` → `[{ user, node_count, total_likes, comment_count }]`
  - 可选 `GET /discovery/books/top`

### 2.2 "谁点赞了"列表

后端 `NodeLike` 有 `(user_id, node_id)`，但没有"列出某节点的点赞者"端点。
前端 StoryNodePage 现在显示 `123 已赞` 是个数字，点不开。

需要：
- `GET /interaction/node/{node_id}/likes` → 分页返回用户列表
- 前端：点赞数字变可点 → 弹层显示"喜欢这个节点的人"

### 2.3 用户作品页

后端有 `GET /story/user/{user_id}/nodes`（`backend/app/api/v1/story.py`），但前端没消费。

- 添加路由：`/user/:userId`
- 显示作者头像 + 简介 + 作品列表（DiscoveryNodeCard 复用）

### 2.4 评论编辑

当前评论只能"删除"（soft delete 到 `deleted_at`）。没有 edit。
**设计选择**：保持极简（只删不改）也是一种风格——避免事后修饰。如果加，需要在 `StoryComment` 加 `edited_at` 字段，前端给作者一个 "编辑" 按钮，编辑后显示 "已编辑" 标记。

### 2.5 评论嵌套回复

完全没有。需要 `StoryComment.parent_id` 自引用 + 前端折叠 UI。**远期**功能。

### 2.6 时间衰减热度

当前 trending 只按 `likes_count` 排序近 N 天发布的节点。
真正的 trending 应该是 **velocity**：`likes_in_last_24h / age_in_hours^1.8` 这种 Hacker News-style 公式。
需要后端在 `NodeLike` 表上 `created_at` 加索引（已经有 `ix_node_likes_node_created`，可复用）。

### 2.7 likes 软删除（一致性）

评论用 soft delete，likes 是真删除。审计/取证场景下应该一致——给 `NodeLike` 加 `deleted_at`，toggle unlike 时改成 update 而不是 delete。优先级低。

### 2.8 评论列表 keyset 分页

当前用 offset/limit。50 条以上的评论 offset 性能会衰减（虽然现实中很难超）。换成 keyset：`WHERE created_at < :cursor ORDER BY created_at DESC`。后端 + 前端都要改。优先级低。

---

## 3. 安全护栏

### 3.1 Rate limit ✅ 已完成（2026-06-03）

两层限流已落地，详见 `changelog.md` 2026-06-03 与 `docs/superpowers/specs/2026-06-03-rate-limiting-design.md`。落地范围：slowapi 应用层（点赞 60/min、评论 6/min 按用户；SSO 换登录态 10/min 按 IP）+ nginx 网络层（写操作按 IP `20r/s burst40`，读请求放过）+ 前端 429 全局提示。**未做（按当时范围决策）**：建节点/上传限流、Redis 共享存储（当前单 worker 内存够用，多 worker/多实例时需换共享后端，否则各算各的）。

原文保留为历史背景：当前任何登录用户可以——
- 每秒几十次 `POST /interaction/node/{id}/like` 切换点赞 → 通知系统会被重复 dedupe 但 PG 仍然写入读取
- 每秒几十次 `POST /interaction/node/{id}/comment` 灌评论

**修法选项**：
- 用 [`slowapi`](https://github.com/laurentS/slowapi)（FastAPI 友好的限流中间件），按 IP + user 维度
- 或在 nginx 层加 `limit_req_zone`
- 推荐 slowapi，因为 nginx 限流不能区分 user

具体阈值建议：
- like toggle：每用户每分钟 60 次
- create comment：每用户每分钟 6 次（避免灌水）

### 3.2 用户屏蔽 / 静音

当前 `User` 只有全站 `banned_until` 字段，没有 user-to-user 关系。
被某用户骚扰时无法屏蔽 ta 的评论/点赞通知。

需要：
- 新表 `user_blocks` (`blocker_id, blocked_id, created_at`)
- 通知发送时跳过被屏蔽用户
- 评论列表过滤被屏蔽用户的评论
- 用户 profile 加"屏蔽"按钮

**远期功能**，运营成熟后再做。

### 3.3 Banned 用户的历史互动

被全站 ban 之后，他们的历史点赞仍然计入 `likes_count`，历史评论仍然显示。
**讨论**：保留还是清除？保留更接近"banned 是禁未来不是改历史"。但若是恶意 spam，应该提供管理员"清除该用户全部互动"的工具。
列入管理后台 todo（不在前端 UI）。

---

## 4. 部署 / 运维

### 4.1 Docker 镜像 chunk size 警告

`frontend/dist/index-*.js` 已经 1.5 MB（gzip 后 426 KB）。Vite 警告超过 500 KB chunk size。
**修法**：在 `vite.config.ts` 加 `build.rollupOptions.output.manualChunks`，把 `naive-ui`、`@tanstack/vue-query`、`vue-router` 分独立 chunk。
不影响功能，只影响初次加载体积。优先级低。

### 4.2 alembic 还没接入

`backend/alembic/versions/` 是空的。当前 schema 演进靠 `auto_migrate.py`（只跑 `create_all`，不破坏）。
新加表/字段时只需要重启容器；改字段类型/加索引就需要手写 alembic migration。
**何时该接**：第一次需要修改已有字段/索引时。在那之前 auto_migrate 够用。

---

## 历史变更

跟踪格式：完成的项从这份文档移除，相应改动写到 `changelog.md`。如果有大跨度的本地优化也可以反向链接到 PR/commit。
