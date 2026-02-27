# Models 数据类型说明

本文档说明 `backend/app/models` 目录中的 ORM 模型数据类型设计，包括：
- SQLAlchemy 2.0 声明式写法
- 枚举类型（Enum）
- 各模型字段类型与业务语义
- 关系（relationship）和常见约束/索引

## 1. 基础约定

### 1.1 Base 基类
- 文件：`base.py`
- `Base` 继承 `DeclarativeBase`，作为所有模型的统一父类。
- 统一使用 `Mapped[T] + mapped_column(...)` 的 SQLAlchemy 2.0 风格声明字段。

### 1.2 常见字段类型
- `String(n)`：短文本（邮箱、用户名、标题等）
- `Text`：长文本（正文、评论内容）
- `Integer`：计数值、ID、排序值
- `Boolean`：开关位（是否激活、是否已读、是否完结）
- `DateTime(timezone=True)`：带时区时间戳（创建、更新时间、审核时间）
- `JSON`：样式扩展或结构化附加数据
- `ForeignKey(...)`：外键关联，常配合 `ondelete` 策略
- `SAEnum(...)`：数据库级枚举约束

---

## 2. 枚举类型（Enums）

### 2.1 auth.py
#### VerificationPurpose
- `register`：注册
- `reset_password`：重置密码
- `change_email`：修改邮箱

### 2.2 user.py
#### UserRole
- `admin`：管理员
- `writer`：普通创作者
- `banned`：封禁用户

### 2.3 interaction.py
#### NotificationType
- `branched`：节点被续写
- `liked`：被点赞
- `commented`：被评论
- `approved`：审核通过
- `rejected`：审核驳回

### 2.4 story_book.py
#### BookPhase
- `drafting`：筹备/内测阶段（可搭建内容框架）
- `writing`：创作阶段（允许持续投稿/分支）
- `showcase`：展示阶段（通常只读展示/互动）
- `archived`：归档阶段（活动结束后的内容沉淀）

### 2.5 story.py
#### NodeStatus
- `pending`：待处理/待发布
- `published`：已发布
- `archived`：归档

#### NodeVisibility
- `private`：私有（通常作者可见）
- `public`：公开（可被常规列表检索）
- `unlisted`：不公开索引（直链可访问）

#### NodeZone
- `long`：长文分区
- `short`：短文分区

---

## 3. 各模型字段说明

## 3.1 EmailVerificationCode（auth.py）
用途：邮箱验证码与过期控制。

关键字段：
- `id: int` 主键
- `email: str` 目标邮箱（索引）
- `purpose: VerificationPurpose` 验证用途（枚举）
- `code: str` 验证码
- `created_at: datetime` 创建时间（默认 `now()`）
- `expires_at: datetime` 过期时间
- `is_used: bool` 是否已使用

类型设计意图：
- 用 `purpose + email` 支持同邮箱多场景验证码并存。
- `expires_at` 与 `is_used` 组合实现幂等与安全校验。

## 3.2 User（user.py）
用途：用户身份、权限和状态管理。

关键字段：
- 标识：`id`, `email`, `username`
- 展示：`display_name`, `bio`, `avatar`
- 权限：`role: UserRole`
- 账号状态：`is_active`, `is_verified`
- 认证：`hashed_password`
- 封禁：`banned_until`, `ban_reason`
- 风控/运营：`trust_level`, `last_login_at`
- 时间：`created_at`, `updated_at`

关系：
- `nodes`（一对多）→ StoryNode
- `likes`（一对多）→ NodeLike
- `comments`（一对多）→ StoryComment
- `notifications`（一对多）→ Notification 接收箱
- `sent_notifications`（一对多）→ Notification 发送记录

约束与索引：
- `email` / `username` 唯一约束
- 用户名长度检查 `length(username) >= 3`
- 常用组合索引：`(is_active, role)`

## 3.3 StoryBook（story_book.py）
用途：故事活动/故事集容器。

关键字段：
- `id: int`
- `title: str` 活动标题
- `description: str | None` 活动描述
- `cover_image: str | None` 封面
- `phase: BookPhase` 活动阶段（替代旧 `is_active`）
- `start_at: datetime | None` 活动开始时间
- `writing_end_at: datetime | None` 创作期结束时间
- `showcase_end_at: datetime | None` 展示期结束时间
- `allow_new_nodes: bool` 是否允许新增节点（运行期开关）
- `created_at: datetime`

关系：
- `nodes`（一对多）→ StoryNode（`cascade="save-update, merge"`，避免误删整棵树）

索引设计：
- `(phase, created_at)`：按阶段管理活动列表
- `(start_at, writing_end_at, showcase_end_at)`：时间线调度与筛选

## 3.4 StoryNode（story.py）
用途：核心故事节点（树结构内容）。

结构字段：
- `id: int`
- `book_id: int` 所属故事集
- `parent_id: int | None` 父节点
- `root_id: int` 根节点 ID（用于聚合/排行榜提速）
- `author_id: int` 作者

内容字段：
- `title: str | None`
- `branch_name: str | None`
- `summary: str | None`
- `content: str`
- `word_count: int`

生命周期/可见性：
- `status: NodeStatus`
- `visibility: NodeVisibility`
- `zone: NodeZone`
- `reviewed_by: int | None`
- `reviewed_at: datetime | None`
- `reject_reason: str | None`
- `published_at: datetime | None`
- `archived_at: datetime | None`
- `archived_reason: str | None`

行为与运营：
- `is_ending: bool` 分支是否完结
- `freeze_interactions: bool` 是否冻结互动
- `is_featured: bool` 是否推荐
- `feature_rank: int | None` 推荐排序

计数字段：
- `likes_count: int`
- `comments_count: int`
- `children_count: int`
- `last_activity_at: datetime`

样式字段：
- `style_key: str | None` 样式模板键
- `style_version: int` 样式版本
- `style_json: dict | None` 样式覆盖 JSON

时间字段：
- `created_at: datetime`
- `updated_at: datetime`

关系：
- `book` → StoryBook
- `author` → User
- `reviewer` → User（审核人）
- `children` / `parent` 自关联树关系

索引设计：
- `(book_id, parent_id, status, visibility, published_at)`：子节点公开查询
- `(book_id, status, visibility, published_at)`：书内最新发布
- `(book_id, status, visibility, likes_count)`：书内热门
- `(root_id, status, visibility, likes_count)`：树内热门

## 3.5 StoryComment（interaction.py）
用途：节点评论（支持软删除）。

关键字段：
- `id: int`
- `book_id: int` 冗余活动ID（便于后台聚合）
- `node_id: int` 所属节点
- `user_id: int | None` 评论作者（可空，兼容用户注销）
- `content: str` 评论文本
- `created_at: datetime`
- `deleted_at: datetime | None`
- `deleted_by: int | None`
- `delete_reason: str | None`

关系：
- `user`（评论作者）
- `node`（所属节点）
- `deleter`（执行删除的用户）

约束与索引：
- 内容非空检查 `length(content) > 0`
- 节点最新评论索引、活动最新评论索引
- 按 `deleted_at` 过滤未删除评论的索引

## 3.6 Notification（interaction.py）
用途：站内通知（行为通知 + 审核通知）。

关键字段：
- `id: int`
- `book_id: int | None`
- `user_id: int` 接收者
- `sender_id: int | None` 触发者
- `type: NotificationType`
- `node_id: int | None`
- `comment_id: int | None`
- `message: str | None` 附加文案
- `dedupe_key: str | None` 去重键
- `is_read: bool`
- `read_at: datetime | None`
- `created_at: datetime`

关系：
- `receiver`（接收用户）
- `sender`（发送用户）
- `node`（目标节点）
- `comment`（目标评论）

约束与索引：
- 目标检查：`node_id/comment_id/message` 至少一项存在
- 未读列表索引：`(user_id, is_read, created_at)`
- 活动维度索引：`(book_id, user_id, created_at)`
- 去重索引：`(user_id, dedupe_key)`

---

## 4. 关系与删除策略（ondelete）

典型策略：
- `CASCADE`：主记录删除时，附属数据一起删除（如评论依附节点）
- `SET NULL`：保留业务数据，仅断开用户关联（如用户被删后评论保留）
- `RESTRICT`：禁止删除仍被引用的数据（如故事节点树结构）

这三种策略结合后，能在“数据完整性、审计留痕、业务可恢复性”之间取得平衡。

---

## 5. 使用建议

- 业务入参尽量使用枚举常量，避免手写字符串。
- `DateTime(timezone=True)` 建议统一按 UTC 写入与比较。
- 高频列表接口优先使用已有组合索引维度（book/status/visibility/published_at 等）。
- 对评论、通知、节点等内容实体，优先软删除或状态迁移，避免不可逆物理删除。

