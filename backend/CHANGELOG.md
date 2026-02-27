# 后端 API 变更说明文档

本文档记录了为适配新版数据模型结构所做的 Schema 和 API 修改。

---

## 1. StoryBook（故事集/活动）相关变更

### 1.1 Schema 变更 (`schemas/story_book.py`)

| 变更类型 | 字段/类 | 说明 |
|---------|--------|------|
| **移除** | `is_active: bool` | 旧版活动开关字段 |
| **新增** | `phase: BookPhase` | 活动阶段枚举（drafting/writing/showcase/archived） |
| **新增** | `start_at: datetime` | 活动开始时间 |
| **新增** | `writing_end_at: datetime` | 创作期结束时间 |
| **新增** | `showcase_end_at: datetime` | 展示期结束时间 |
| **新增** | `allow_new_nodes: bool` | 是否允许新增节点（运行期开关） |

**影响范围：**
- `StoryBookCreate`：新增 `phase`, `start_at`, `writing_end_at`, `showcase_end_at`, `allow_new_nodes` 字段
- `StoryBookUpdate`：移除 `is_active`，新增上述字段
- `StoryBookResponse`：同上

### 1.2 API 变更 (`api/v1/story.py`)

| 接口 | 变更内容 |
|-----|---------|
| `POST /books` | 移除 `is_active=True` 硬编码，改用 schema 传入的 `phase`（默认 `DRAFTING`） |
| `GET /books` | 移除 `is_active == True` 过滤，改为 `phase != ARCHIVED`；新增 `phase` 查询参数支持按阶段筛选 |
| `PATCH /books/{book_id}` | 支持更新 `phase` 及时间线字段 |

---

## 2. StoryNode（故事节点）相关变更

### 2.1 Schema 变更 (`schemas/story.py`)

| 变更类型 | 字段/类 | 说明 |
|---------|--------|------|
| **移除** | `depth: int` | 旧版深度字段（模型中已不存在） |
| **新增** | `root_id: int` | 根节点 ID，用于树聚合/热榜 |
| **新增** | `visibility: NodeVisibility` | 可见性（private/public/unlisted） |
| **新增** | `zone: NodeZone` | 展区（featured_long/brainstorm_short） |
| **新增** | `word_count: int` | 字数统计 |
| **新增** | `comments_count: int` | 评论数 |
| **新增** | `children_count: int` | 子节点数 |
| **新增** | `is_ending: bool` | 分支是否完结 |
| **新增** | `is_featured: bool` | 是否推荐 |
| **新增** | `published_at: datetime` | 发布时间 |
| **新增** | `reject_reason: str` | 驳回原因 |
| **新增** | `archived_reason: str` | 归档原因 |
| **新增** | `reviewed_at: datetime` | 审核时间 |

**影响范围：**
- `StoryNodeCreate`：新增 `zone`, `summary` 字段
- `StoryNodeListItem`：移除 `depth`，新增 `root_id`, `visibility`, `zone`, `word_count`, `comments_count`, `children_count`, `is_ending`, `is_featured`, `published_at`
- `StoryNodeRead`：新增 `reject_reason`, `archived_reason`, `reviewed_at`
- `NodeAuditRequest`：新增 `reject_reason` 字段

### 2.2 API 变更 (`api/v1/story.py`)

| 接口 | 变更内容 |
|-----|---------|
| `POST /node` | 1. 活动检查改为 `book.phase == WRITING` + `book.allow_new_nodes`<br>2. 移除 `depth` 字段赋值<br>3. 新增 `root_id` 计算（根节点为自身 ID）<br>4. 新增 `word_count` 自动计算<br>5. 新增 `visibility` 初始值设置 |
| `GET /tree` | 权限过滤逻辑重构，使用 `_visible_filter()` 辅助函数 |
| `GET /node/{node_id}/path` | SQL 排序从 `depth ASC` 改为 `id ASC` |
| `GET /node/{node_id}` | 权限检查使用 `_is_node_visible()` 辅助函数 |
| `DELETE /node/{node_id}` | 软删除状态从 `REJECTED` 改为 `ARCHIVED`，设置 `archived_at` 和 `archived_reason` |

### 2.3 权限规则变更

**新权限规则：**
- `published` 状态：所有人可见
- `pending` / `archived` 状态：仅管理员和作者本人可见

**实现方式：**
- 新增 `_is_node_visible()` 辅助函数
- 新增 `_visible_filter()` SQLAlchemy 过滤器

---

## 3. Notification（通知）相关变更

### 3.1 Schema 变更 (`schemas/interaction.py`)

| 变更类型 | 字段 | 说明 |
|---------|------|------|
| **移除** | `target_id: int` | 旧版统一目标 ID |
| **新增** | `node_id: int` | 关联节点 ID |
| **新增** | `comment_id: int` | 关联评论 ID |
| **新增** | `message: str` | 附加文案（驳回原因/系统提示） |

### 3.2 工具函数变更 (`utils/notification.py`)

**旧版签名：**
```python
async def send_notification(
    db, sender_id, receiver_id, type, target_id
)
```

**新版签名：**
```python
async def send_notification(
    db, receiver_id, type,
    sender_id=None, node_id=None, comment_id=None,
    message=None, book_id=None, dedupe_key=None
)
```

**变更说明：**
- `sender_id` 改为可选（系统通知可为空）
- `target_id` 拆分为 `node_id` / `comment_id`
- 新增 `message` 支持附加文案
- 新增 `book_id` 支持按活动聚合
- 新增 `dedupe_key` 支持去重

### 3.3 API 变更 (`api/v1/interaction.py`)

| 接口 | 变更内容 |
|-----|---------|
| `POST /node/{node_id}/like` | `send_notification` 调用改用新参数签名，新增 `dedupe_key` |
| `POST /node/{node_id}/comment` | 1. 新增 `book_id=node.book_id` 冗余字段<br>2. `send_notification` 调用改用新参数签名 |
| `GET /node/{node_id}/comments` | 新增 `deleted_at IS NULL` 过滤，排除软删除评论 |

---

## 4. Admin（管理后台）相关变更

### 4.1 API 变更 (`api/v1/admin.py`)

| 接口 | 变更内容 |
|-----|---------|
| `PATCH /nodes/{node_id}/audit` | 1. 审核通过时设置 `published_at`, `visibility=PUBLIC`<br>2. 审核归档时设置 `archived_at`, `archived_reason`<br>3. 设置 `reviewed_by`, `reviewed_at`<br>4. `send_notification` 调用改用新参数签名，支持 `message` 传递驳回原因 |

---

## 5. 枚举值变更

### 5.1 NodeZone

| 旧值 | 新值 |
|-----|-----|
| `LONG` | `featured_long` |
| `SHORT` | `brainstorm_short` |

### 5.2 NodeStatus

| 变更类型 | 值 |
|---------|---|
| 保留 | `pending`, `published`, `archived` |
| 移除 | `rejected`（归档状态替代） |

---

## 6. 数据库迁移注意事项

本次修改涉及模型字段变更，需要创建 Alembic 迁移脚本：

1. `story_books` 表：
   - 删除 `is_active` 列
   - 新增 `phase`, `start_at`, `writing_end_at`, `showcase_end_at`, `allow_new_nodes` 列

2. `story_nodes` 表：
   - 删除 `depth` 列（如果存在）
   - 新增 `root_id` 列（必填，需回填现有数据）

3. `notifications` 表：
   - 删除 `target_id` 列（如果存在）
   - 新增 `node_id`, `comment_id`, `message`, `book_id`, `dedupe_key` 列

---

## 7. 前端适配建议

1. **活动列表**：`is_active` 字段已移除，改用 `phase` 判断活动状态
2. **节点列表**：移除 `depth` 字段依赖，改用 `root_id` 进行树聚合
3. **通知跳转**：`target_id` 已拆分为 `node_id` / `comment_id`
4. **审核状态**：`rejected` 状态已移除，改用 `archived` 状态

---

*文档生成时间：2026-02-19*