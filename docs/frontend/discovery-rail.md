# 发现栏组件与榜单/推荐数据契约

## 目标

这份文档定义两件事：

- 前端如何复用同一套“发现栏 / 推荐栏”组件
- 后端以后新增榜单、推荐、精选接口时，返回结构最好如何统一

当前约定优先服务于“节点类内容推荐”，因为平台的发现对象目前主要还是 `StoryNode`。

## 前端组件结构

当前已经落地的基础组件：

- `frontend/src/components/discovery/DiscoveryRail.vue`
  - 通用发现栏容器
  - 负责标题、描述、加载态、错误态、空态、列表布局
- `frontend/src/components/discovery/DiscoveryNodeCard.vue`
  - 通用节点推荐卡
  - 负责节点摘要、徽标、指标、主操作按钮

这两个组件的原则是：

- 统一展示结构
- 不绑定具体数据来源
- 页面负责 query 和数据映射
- 组件只负责展示

## 前端标准化数据类型

前端统一类型定义在：

- `frontend/src/types/discovery.ts`

当前核心类型：

### `DiscoveryRailItem`

用于组件层展示的标准卡片数据。

```ts
interface DiscoveryRailItem {
  id: string | number
  title: string
  summary: string
  badge: string
  badgeTone?: 'default' | 'strong'
  meta: string[]
  metrics?: Array<{ label: string; value: string }>
  hint?: string
  action: {
    label: string
    to: string
  }
  status?: 'published' | 'pending' | 'archived' | 'neutral'
}
```

含义：

- `title`
  - 卡片主标题
- `summary`
  - 摘要文本
- `badge`
  - 右上角短标签，例如 `已发布`、`Likes 12`、`Book 3`
- `meta`
  - 次级元信息，例如作者、发布时间
- `metrics`
  - 可选指标区，例如评论数、分支数、点赞数
- `hint`
  - 底部提示
- `action`
  - 主按钮行为

建议：

- 页面层把后端原始数据先映射成 `DiscoveryRailItem`
- 组件层不要直接依赖后端原始 JSON

## 后端推荐接口建议契约

当前后端已经有：

- `/api/v1/discovery/featured`
- `/api/v1/discovery/feed`
- `/api/v1/discovery/trending`
- `/api/v1/discovery/search`

它们现在直接返回 `StoryNodeListItem[]`，这在第一阶段是可以接受的。  
但如果后面要继续扩展“精选”“值得续写”“完结推荐”“热门分支”等能力，建议逐步收口到统一的 section 响应格式。

推荐的后端返回结构：

```json
{
  "section_key": "trending_nodes",
  "title": "热门节点",
  "description": "最近 7 天点赞最高的已发布节点",
  "algorithm_key": "likes_last_7d",
  "items": [
    {
      "id": 123,
      "parent_id": 45,
      "root_id": 1,
      "book_id": 7,
      "author": {
        "id": 5,
        "username": "writer_a",
        "avatar": null
      },
      "title": "节点标题",
      "summary": "节点摘要",
      "status": "published",
      "visibility": "public",
      "zone": "short",
      "word_count": 320,
      "likes_count": 18,
      "comments_count": 6,
      "children_count": 4,
      "is_ending": false,
      "freeze_interactions": false,
      "is_featured": false,
      "published_at": "2026-04-02T08:00:00Z",
      "created_at": "2026-04-02T08:00:00Z",
      "updated_at": "2026-04-02T08:00:00Z"
    }
  ]
}
```

也就是说：

- `items` 仍然优先复用现有 `StoryNodeListItem`
- 外层再包一层 section 元信息

## 为什么推荐这样设计

原因有三个：

1. 前端发现栏可以只换数据源，不换结构。
2. 后端不同榜单可以共享统一响应格式。
3. 后续如果要把一个页面做成“多栏发现页”，前端可以直接渲染多个 section。

## 建议的后端演进顺序

为了不做大改，建议按这个顺序演进：

1. 第一阶段
   - 保持现有 `/featured`、`/feed`、`/trending`、`/search` 直接返回 `StoryNodeListItem[]`
   - 前端页面自己映射成 `DiscoveryRailItem`

2. 第二阶段
   - 新增更偏运营或推荐的接口时，开始使用 `DiscoverySectionResponse`
   - 比如：
     - `featured_nodes`
     - `recommended_to_continue`
     - `completed_branches`

3. 第三阶段
   - 如果首页或发现页需要一次拿多栏内容，可以再增加聚合接口，例如：
   - `GET /api/v1/discovery/home`
   - 返回多个 section 数组

## 当前结论

现在最重要的不是立刻发明复杂推荐算法，而是：

- 前端先用统一组件和统一卡片结构
- 后端以后新增榜单时，优先遵守统一 section 契约

这样平台的发现系统才能持续扩展，而不是每加一个榜单就长一套新模板和新 JSON 结构。
