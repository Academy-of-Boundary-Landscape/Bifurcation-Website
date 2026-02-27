// 用户角色枚举
export type UserRole = 'admin' | 'writer' | 'banned'

// 用户相关类型
export interface User {
  id: number
  email: string
  username: string
  avatar?: string | null
  bio?: string | null
  role: UserRole
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

// 用户概要信息（在列表中使用）
export interface AuthorInfo {
  id: number
  username: string
  avatar?: string | null
}

// 用户详情响应（包含统计信息）
export interface UserProfile extends User {
  nodes_count: number
  likes_count: number
}

// 节点状态枚举
export type NodeStatus = 'pending' | 'published' | 'archived'

// 节点可见性
export type NodeVisibility = 'private' | 'public' | 'unlisted'

// 节点分区
export type NodeZone = 'long' | 'short'

// 活动阶段
export type BookPhase = 'drafting' | 'writing' | 'showcase' | 'archived'

// 故事书/活动类型
export interface StoryBook {
  id: number
  title: string
  description?: string | null
  cover_image?: string | null
  phase: BookPhase
  start_at?: string | null
  writing_end_at?: string | null
  showcase_end_at?: string | null
  allow_new_nodes: boolean
  created_at: string
}

// 节点列表项（用于 Feed、搜索、用户创作列表，不含 children 和 content）
export interface StoryNodeListItem {
  id: number
  parent_id?: number | null
  root_id: number
  book_id: number
  author: AuthorInfo
  title?: string | null
  summary?: string | null
  branch_name?: string | null
  status: NodeStatus
  visibility: NodeVisibility
  zone: NodeZone
  word_count: number
  likes_count: number
  comments_count: number
  children_count: number
  is_ending: boolean
  is_featured: boolean
  published_at?: string | null
  created_at: string
  updated_at: string
}

// 节点详情（用于阅读页面，包含 content，但仍不含 children）
export interface StoryNodeRead {
  id: number
  parent_id?: number | null
  root_id: number
  book_id: number
  author: AuthorInfo
  title?: string | null
  summary?: string | null
  branch_name?: string | null
  status: NodeStatus
  visibility: NodeVisibility
  zone: NodeZone
  word_count: number
  likes_count: number
  comments_count: number
  children_count: number
  is_ending: boolean
  is_featured: boolean
  published_at?: string | null
  created_at: string
  updated_at: string
  content: string
  reject_reason?: string | null
  archived_reason?: string | null
  reviewed_at?: string | null
}

// 节点树形项（用于故事树展示，包含 children 递归，不含 content）
export interface StoryNodeTreeItem {
  id: number
  parent_id?: number | null
  root_id: number
  book_id: number
  author: AuthorInfo
  title?: string | null
  summary?: string | null
  branch_name?: string | null
  status: NodeStatus
  visibility: NodeVisibility
  zone: NodeZone
  word_count: number
  likes_count: number
  comments_count: number
  children_count: number
  is_ending: boolean
  is_featured: boolean
  published_at?: string | null
  created_at: string
  updated_at: string
  children: StoryNodeTreeItem[]
}

// 互动相关类型
export interface Comment {
  id: number
  node_id: number
  book_id: number
  content: string
  created_at: string
  deleted_at?: string | null
  user?: AuthorInfo | null
}

// 通知类型枚举（兼容文档与后端实现中的命名差异）
export type NotificationType =
  | 'like'
  | 'comment'
  | 'reply'
  | 'audit'
  | 'liked'
  | 'commented'
  | 'branched'
  | 'approved'
  | 'rejected'

export interface Notification {
  id: number
  type: NotificationType
  sender?: AuthorInfo | null
  node_id?: number | null
  comment_id?: number | null
  message?: string | null
  is_read: boolean
  created_at: string
}