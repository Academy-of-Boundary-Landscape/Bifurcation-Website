# 后端核心正确性审计 — 03 数据完整性与指标可信度

> 范围：`backend/app/services/{interactions,story_nodes,sso}.py`、`backend/app/models/{story,story_book,interaction,user}.py`、`backend/app/api/v1/{discovery,admin,story,interaction,users,auth}.py`
> 主题：平台"指标说谎"——审计冗余计数、聚合统计、软删除一致性、热榜排序是否诚实。
> 模式：只读审计，未改动任何源码。
> 交叉对照：`docs/followups.md`（标注哪些是已知、哪些是新发现）。

---

## 一、计数完整性（denormalized counters）

### 【高】点赞/评论计数的 read-modify-write 竞态 —— 会导致 likes_count / comments_count 长期失真
- `backend/app/services/interactions.py:47`（`node.likes_count += 1`）、`:43`（`-= 1`）
- `backend/app/services/interactions.py:92`（`node.comments_count += 1`）
- `backend/app/api/v1/interaction.py:271`（删评论 `node.comments_count -= 1`）
- `backend/app/api/v1/story.py:593`（删节点 `parent_node.children_count -= 1`）
- `backend/app/services/story_nodes.py:90`（建节点 `parent_node.children_count += 1`）

**问题**：全部是"先把整行读进 ORM 实例（`db.get`），在 Python 里 `+= 1`，再 commit"。两个并发请求会读到同一旧值、各自 +1、后写覆盖先写，丢一次计数。SQLAlchemy 默认 `READ COMMITTED` 隔离级别下 ORM 不会自动转成 `SET x = x + 1` 的原子 UPDATE，因此 race 真实存在。

**为什么重要**：这些字段就是页面上显示给用户看的"点赞数/评论数/分支数"，也是热榜（见第四节）和 `StoryNodeListItem` 列表项（`schemas/story.py:61-63`）的数据源。一旦漂移，**显示的指标直接说谎**，且没有任何对账/重算（reconciliation）机制把它们拉回真实行数。漂移只会单调累积，永不自愈。

**对照 followups**：已知项 followups.md §1.1 已精确点名 `interactions.py:47/43/92`。本次**新增**确认同类问题还存在于 `interaction.py:271`（删评论）、`story.py:593`（删节点）、`story_nodes.py:90`（建节点 children_count），followups 未覆盖这三处。

**修法**：
```python
await db.execute(
    update(StoryNode).where(StoryNode.id == node_id)
    .values(likes_count=StoryNode.likes_count + 1)
)
# 减法兜底防负数（PG）：
.values(likes_count=func.greatest(StoryNode.likes_count - 1, 0))
```
commit 后若要返回新值需 `await db.refresh(node, attribute_names=["likes_count"])`。另外建议加一个离线对账脚本/管理端点，用 `COUNT(*)` 周期性校正所有计数列。

### 【中】计数与"主数据写入"不在同一原子语义下，仍可漂移
- `backend/app/services/story_nodes.py:80-92`：`db.add(new_node)` → `flush` → 父节点 `children_count += 1` → `commit`。子节点行与父计数在同一事务，单看 OK；但与上面的并发问题叠加，children_count 仍会丢。
- `backend/app/services/interactions.py:46-47`：插入 `NodeLike` 与 `likes_count += 1` 同事务，唯一约束 `uq_node_likes_user_node` 能挡重复点赞行，但**计数列本身没有约束**，漂移后无法靠 DB 约束发现。

### 【中】children_count 语义不一致：建节点时不分状态全部计入，删节点时只在"非 archived→archived"时回收
- 建：`story_nodes.py:88-90` 无论新节点是 PENDING 还是 PUBLISHED 都给父 `children_count += 1`。
- 删：`story.py:587-594` 软删（→archived）时回收 1；但若节点本就被审核 ARCHIVED（`audit_story_node_record`，`story_nodes.py:147-152`）**不会**回收 children_count；审核把 PENDING→PUBLISHED 也不动计数（正确，因为建时已计）。
- 结果：被管理员归档/驳回的节点，其父的 `children_count` 永远偏高。`children_count` 含义因此变成"历史上挂过的子节点数（含已归档）"，而树接口（`/tree`）按可见性过滤后实际显示的子节点数会比这个值小 —— **显示的分支数对不上实际能点开的分支数**。

---

## 二、/admin/stats 聚合正确性

### 【中】users.active 统计的是 `is_active`，与"封禁"语义脱节，dashboard 的"活跃用户"偏高
- `backend/app/api/v1/admin.py:241`：`users_active = count(User.is_active == True)`。
- 问题：封禁有两套机制 —— `User.role == BANNED`（`models/user.py:19`）和 `User.banned_until`（`models/user.py:54`、`is_banned()` 方法 `:112`）。一个被 `role=BANNED` 或 `banned_until` 在未来的用户，只要 `is_active` 仍为 True，就会被计入"活跃"。`inactive = total - active`（`:265`）同样不反映封禁人数。
- 影响：后台"活跃用户数"虚高，"封禁/受限用户"在 dashboard 上完全不可见。属于**指标说谎**的一类。
- 修法：明确口径。若"活跃"= 可正常使用，应 `where(is_active==True, role != BANNED, or_(banned_until==None, banned_until <= now))`；或单独再出一个 `banned` 计数。

### 【低】nodes_total 包含 archived（含用户软删除的节点），"节点总数"含义偏运营内部
- `backend/app/api/v1/admin.py:243`：`nodes_total = count(全部)`，含 ARCHIVED。
- 这本身不算错（确实是总行数），但与前台/用户感知的"作品数"不一致。`nodes` 分组里同时给了 pending/published/archived 拆分（`:244-252`），口径自洽，故评低。注意 `total` 不等于 `pending+published+archived` 仅当出现枚举外状态时——当前枚举封闭，等式成立。

### 【低】new_nodes_7d / new_users_7d 用 created_at，不区分状态
- `backend/app/api/v1/admin.py:254-259`：近 7 天新增节点计入了 pending 和已被驳回 archived 的。作为"投稿活跃度"可接受，作为"新增内容"会偏高。属口径说明问题，非 bug。

**小结**：/admin/stats 没有双重计数、没有 join 误差（都是单表 count），主要问题是**"活跃"口径未排除封禁**（中）。

---

## 三、软删除一致性

### 【中】comments_count 包含历史脏数据：删评论靠应用层 -1，没有重算，漂移后含已软删评论
- 软删评论：`backend/app/api/v1/interaction.py:261` 置 `deleted_at`，`:271` 给节点 `comments_count -= 1`（仅当 >0）。
- 列表读取：`backend/app/api/v1/interaction.py:69` 正确 `where(deleted_at.is_(None))` 过滤软删。
- 一致性 OK 的前提：每次软删都成功 -1。但因为 -1 也是 read-modify-write（第一节【高】），并发或历史漂移会让 `comments_count` 与"未软删评论真实行数"对不上。展示页直接吃 `comments_count`（`schemas/story.py:62`），而评论列表只显示未删的 —— **顶部"N 条评论"与下面实际列出的条数可能不一致**。
- 修法：要么把 `comments_count` 改成实时 `COUNT(*) WHERE deleted_at IS NULL`（节点详情/树一次性聚合），要么定期对账。

### 【低】likes 是硬删除、comments 是软删除（口径不统一）
- `backend/app/services/interactions.py:41` `db.delete(existing_like)`（硬删）vs 评论软删。
- 取证/审计场景不一致，followups.md §2.7 已知（优先级低）。对**计数正确性无直接影响**，因为 likes_count 用 -1 跟随；但意味着"谁点过赞又取消"不可追溯。

### 【低】节点软删除（→archived）后其评论/点赞计数与可见性
- `story.py:581` 把节点设 ARCHIVED，但**不清理**该节点的评论/点赞，也不回收作者维度的统计。前台 profile 的 likes/nodes 统计已用 `WHERE status==PUBLISHED` 过滤（见第二节 users.py），所以 archived 节点的赞不计入主页——**这是对的**。但 `auth.py /me`（见下）口径不同。

---

## 四、Trending / Discovery 排序诚实性

### 【高】/trending 不是"近期热度"，而是"近 N 天发布的节点按历史总赞排序" —— 标签与实现不符
- `backend/app/api/v1/discovery.py:121-130`：窗口条件是 `created_at >= start_date`（**节点的创建时间**），排序是 `desc(likes_count)`（**该节点历史累计总赞**，不是窗口内新增的赞）。
- 问题：
  1. 一个 7 天前点赞、但昨天才发布的节点……不存在；但反过来，**一个昨天发布、靠老粉一次性刷上去的节点**和**一个持续被点赞的节点**没有区别，纯按总赞。窗口只过滤"哪些节点参与排序"，不衡量"窗口内的热度"。
  2. `likes_count` 本身就可能漂移（第一节【高】），所以 trending 排序建立在**可能说谎的字段**上。followups.md §1.1 明确警告"做 leaderboard / 热门之前必须修"，而热门接口已经上线在用。
  3. 兜底逻辑 `discovery.py:136-145`：近期不足 3 条就退回"历史总榜"，此时 `days` 窗口完全失效，用户看到的"近 7 日热门"其实是 all-time 榜，**且无任何前端可感知的标识**。
- 影响：这是最典型的"指标说谎"——UI 文案/接口 summary 都叫"热门趋势/近 7 日"，但排序既不反映近期、也依赖会漂移的计数。
- **对照 followups**：§2.6"时间衰减热度"已知应改成 velocity 公式（`likes_in_last_24h / age^1.8`），但当前实现连"窗口内点赞数"都没统计。本审计**强化**该结论：现状不仅缺时间衰减，连基本的"窗口内增量"都不是。
- 修法：用 `NodeLike.created_at`（已有索引 `ix_node_likes_node_created`）在窗口内 `COUNT` 实时点赞数排序：
  ```sql
  SELECT n.*, COUNT(l.id) AS recent_likes
  FROM story_nodes n
  LEFT JOIN node_likes l ON l.node_id = n.id AND l.created_at >= :start
  WHERE n.status='published'
  GROUP BY n.id ORDER BY recent_likes DESC
  ```
  进一步可加 HN 衰减。这样 trending 不再依赖 `likes_count` 冗余列。

### 【中】/search 与 /featured 也按 `likes_count` 排序，继承冗余列漂移风险
- `backend/app/api/v1/discovery.py:183`（search）、`featured` 用 feature_rank 不依赖计数（`:46-50`，OK）。
- search 按 `likes_count` 倒序在计数漂移时排序失真，但搜索场景容忍度高，评中。

### 【低】/feed 用 created_at 倒序，但 trending 用 created_at 做窗口、published 节点 created_at 可能早于 published_at
- 节点 `created_at` 在投稿时即写入（PENDING），`published_at` 在审核通过时才写（`story_nodes.py:77/141`）。`/feed`（`discovery.py:85`）和 `/trending` 窗口（`:127`）都用 `created_at`，意味着**一篇投稿很久、刚通过审核的节点**，按 created_at 会排在很后面，可能根本进不了"最新"和"近 7 日"窗口。对"最新发布"语义而言应该用 `published_at`。属口径 bug，影响中等偏低。

---

## 五、N+1 / 性能

### 【低/良好】列表与树接口普遍用 selectinload(author)，无明显 N+1
- `/feed`、`/trending`、`/search`、`/featured`、`/tree`、`/node`、`admin /nodes` 都 `selectinload(StoryNode.author)`，author 不会 N+1。
- `/tree`（`story.py:233-245`）额外用 `defer(content)` 避免拉大正文、`raiseload(children)` 防呆，`build_memory_tree`（`:66-90`）纯内存组树——**写得不错**。

### 【低】/node/{id}/path 递归 CTE + 二次批量查作者，OK
- `story.py:311-340`：用 `WHERE id IN (author_ids)` 一次性批量取作者，无循环单查。良好。

### 【低】comments / notifications 用 offset/limit，深翻页会退化
- `interaction.py:73` 评论、`:132` 通知。followups.md §2.8 已知（低）。当前数据量无碍。

### 【中】profile 统计每次实时 COUNT + JOIN（users.py / auth.py），无缓存
- `users.py:40-55`、`auth.py:70-82`：每次查主页都跑 2 个聚合（其中点赞数走 `NodeLike JOIN StoryNode`）。单次可接受，热门用户主页高频访问时可能成热点。非正确性问题。

---

## 六、可见性 / 权限过滤一致性

### 【中】profile 统计口径不一致：`/users/{id}` 只算 PUBLISHED，`/auth/me` 算全部状态
- `backend/app/api/v1/users.py:43/53`：他人主页 `nodes_count` 和 `likes_count` 都 `WHERE status==PUBLISHED`（正确——不该把别人的 pending/archived 暴露给访客，也不该计入）。
- `backend/app/api/v1/auth.py:70-82`：`/me` 的 `nodes_count`、`likes_count`**没有任何 status 过滤**，把自己的 pending/archived 节点和这些节点收到的赞都算进去。
- 影响：同一个用户，自己看自己主页（/me）和别人看 ta 主页（/users/{id})，**节点数和获赞数会不一样**——这就是指标不一致。/me 偏高（含未发布/已驳回）。属于轻度"指标说谎"。
- 修法：统一口径。要么 /me 也 `WHERE status==PUBLISHED`（推荐，对外口径），要么 /me 额外分列"已发布 vs 待审/已归档"。

### 【低/良好】节点可见性过滤跨端点基本一致
- `_visible_filter` / `_is_node_visible`（`story.py:31-63`）统一规则：published 全可见，pending/archived 仅 admin 和作者本人。`/tree`、`/node`（children）、`/node/{id}`、`/node/{id}/path`(递归 CTE 内联同款条件) 都套用。良好。
- `read_user_nodes`（`story.py:475-481`）单独实现同语义（admin/self 可带 status 过滤，他人仅 published），一致。

### 【中】NodeVisibility 维度（PUBLIC/PRIVATE/UNLISTED）在读路径上几乎被忽略，只看 status
- 模型有 `visibility` 列且建了组合索引（`models/story.py:78-83, 164-170`），审核流程也维护它（`story_nodes.py:76/142/148`）。
- 但所有读端点（discovery 全部、story tree/children/detail/path）**只过滤 `status`，从不过滤 `visibility`**。当前 status 与 visibility 同步变更（published↔public、pending/archived↔private），所以暂时不出 bug。但 `UNLISTED`（"直链可见不进列表"）这个设计**完全没有被实现**——一个 UNLISTED 节点如果 status=PUBLISHED 会照常出现在 feed/trending/tree 列表里。
- 影响：visibility 是死维度，未来若真用到 UNLISTED 会直接漏。当前评中（潜在数据暴露/语义未实现）。

### 【低】discovery 端点不校验 book.phase，archived 活动的节点仍出现在全站 feed/trending/search
- `/feed`、`/trending`、`/search`（discovery.py）只按节点 status 过滤，不看所属 book 的 phase。`read_books`（`story.py:178`）默认隐藏 ARCHIVED 活动，但单个节点仍能通过 discovery 浮现。是否期望取决于产品定义，标低。

---

## 七、其他（SSO / 数据完整性附带发现）

### 【低】SSO 角色每次登录跟随 claim 同步，可悄悄降权管理员
- `backend/app/services/sso.py:266-270`：除 BANNED 外，每次登录都 `user.role = resolved_role`。若某次 Casdoor claim 缺 admin 角色（或 userinfo 拉取顺序导致 claim 不全），管理员会被静默降为 WRITER。`_resolve_claims`（`:355-359`）用 userinfo 覆盖 id_token，userinfo 失败时仅回退 id_token，admin claim 可能丢失。非本审计核心（指标）范畴，记录备查。

### 【低】auth 邮箱自动绑定的并发与多账号
- `sso.py:300-312`：`SSO_AUTO_LINK_BY_EMAIL` 下用 email 匹配本地用户，已处理"多账号"和"管理员不可邮箱绑定"。`User.email` 无唯一约束（`models/user.py:28` 仅 index），靠应用层 `len>1` 判断。并发首次登录可能创建两条同 email 用户。低概率，记录。

---

## 优先级建议（前 5）

1. **【高】修复 trending 排序的"说谎"**（`discovery.py:121-130`）：改为按窗口内 `NodeLike.created_at` 实时 COUNT 排序，摆脱对可漂移的 `likes_count` 的依赖；并给"兜底退回 all-time"加可见标识或参数。这是最直接的指标可信度问题。
2. **【高】计数原子化 + 对账**（`interactions.py:43/47/92`、`interaction.py:271`、`story.py:593`、`story_nodes.py:90`）：全部改 `UPDATE ... SET x = x + 1`（减法用 `greatest(..,0)`），并加一个 `COUNT(*)` 周期对账脚本。followups §1.1 已记录前三处，补齐后三处。
3. **【中】统一 profile 统计口径**（`auth.py:70-82` vs `users.py:43/53`）：让 /me 与他人主页一致（建议都按 PUBLISHED），消除"自己看自己 vs 别人看自己"指标不一致。
4. **【中】comments_count 与软删一致性**（`interaction.py:271` + 展示侧）：改为实时 `COUNT(*) WHERE deleted_at IS NULL` 或纳入对账，避免顶部计数与列表条数对不上。同时修 children_count 在管理员归档路径（`story_nodes.py:147`）不回收的问题。
5. **【中】/admin/stats "活跃用户"口径**（`admin.py:241/265`）：排除 `role==BANNED` 与 `banned_until>now`，或单列封禁数，让 dashboard 不虚报活跃。

---

## 关键结论：哪些指标在"说谎"

- 「热门 / 近 7 日趋势」：窗口只筛节点、排序吃历史总赞且可能漂移、冷场时静默退化为 all-time 榜。
- 「点赞数 / 评论数 / 分支数」：靠 read-modify-write 维护，并发丢更新、无对账，单调漂移。
- 「评论数 vs 实际评论列表」：计数含历史软删脏数据，可与列出条数不符。
- 「我的获赞/作品数 vs 他人看我的」：/me 含 pending/archived，/users/{id} 只含 published，两边对不上。
- 「分支数 vs 树里能点开的分支」：children_count 含已归档子节点，比可见子节点多。
- 「后台活跃用户数」：含被 role/banned_until 封禁但 is_active 仍为 True 的用户，虚高。
