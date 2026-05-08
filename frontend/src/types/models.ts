// 用户角色
export type UserRole = 'admin' | 'writer' | 'banned'

// 节点状态
export type NodeStatus = 'pending' | 'published' | 'archived'
export type NodeVisibility = 'private' | 'public' | 'unlisted'
export type NodeZone = 'long' | 'short'
export type BookPhase = 'drafting' | 'writing' | 'showcase' | 'archived'

// 用户
export interface User {
  id: number
  email: string
  username: string
  role: UserRole
  is_active: boolean
  bio: string | null
  avatar: string | null
  nodes_count?: number
  likes_count?: number
  created_at: string
  updated_at: string
}

export interface UserCreate {
  email: string
  username: string
  password: string
}

export interface UserUpdate {
  username?: string | null
  bio?: string | null
  avatar?: string | null
}

export interface UserProfileResponse extends User {
  nodes_count?: number
  likes_count?: number
}

// 故事册
export interface StoryBook {
  id: number
  title: string
  description: string | null
  cover_image: string | null
  is_active: boolean
  phase: BookPhase
  allow_new_nodes: boolean
  start_at: string | null
  writing_end_at: string | null
  showcase_end_at: string | null
  created_at: string
  updated_at: string
  nodes_count?: number
}

export interface StoryBookCreate {
  title: string
  description?: string | null
  cover_image?: string | null
  phase?: BookPhase
  start_at?: string | null
  writing_end_at?: string | null
  showcase_end_at?: string | null
  allow_new_nodes?: boolean
}

// 作者信息
export interface AuthorInfo {
  id: number
  username: string
  avatar: string | null
}

// 故事节点
export interface StoryNode {
  id: number
  parent_id: number | null
  root_id: number
  book_id: number
  author: AuthorInfo
  title: string | null
  summary: string | null
  branch_name: string | null
  status: NodeStatus
  visibility: NodeVisibility
  zone: NodeZone
  word_count: number
  likes_count: number
  comments_count: number
  children_count: number
  is_ending: boolean
  freeze_interactions: boolean
  is_featured: boolean
  feature_rank: number | null
  published_at: string | null
  created_at: string
  updated_at: string
}

export interface StoryNodeRead extends StoryNode {
  content: string
  reject_reason: string | null
  archived_reason: string | null
  reviewed_by?: number | null
  reviewed_at: string | null
  /** 当前请求用户是否已点赞此节点；匿名访问永远是 false。后端在 GET /node/:id 上注入。 */
  is_liked: boolean
}

export interface StoryNodeCreate {
  book_id: number
  parent_id?: number | null
  title?: string | null
  content: string
  branch_name?: string | null
  summary?: string | null
  zone: NodeZone
}

export interface StoryNodeTreeItem extends StoryNode {
  children: StoryNodeTreeItem[]
}

// 评论
export interface Comment {
  id: number
  node_id: number
  book_id: number
  content: string
  created_at: string
  deleted_at: string | null
  user: AuthorInfo | null
}

export interface CommentCreate {
  content: string
}

// 通知
export interface Notification {
  id: number
  type: 'branched' | 'liked' | 'commented' | 'approved' | 'rejected'
  sender: AuthorInfo | null
  node_id: number | null
  comment_id: number | null
  message: string | null
  is_read: boolean
  created_at: string
}

// 点赞
export interface LikeToggleResponse {
  status: string
  action: 'liked' | 'unliked'
  likes_count: number
}

// 审核请求
export interface NodeAuditRequest {
  status: NodeStatus
  reject_reason?: string | null
}

// 前端扩展类型（用于页面展示）
export interface StoryNodeWithBookTitle extends StoryNodeRead {
  book_title: string | null
}

// 用户通知统计
export interface UserNotificationsSummary {
  unread_count: number
  total_count: number
}

// 通知统计响应
export interface NotificationCountResponse {
  unread_count: number
}

// 管理员统计数据
export interface AdminDashboardStats {
  users: {
    total: number
    active: number
    inactive: number
    new_7d: number
  }
  nodes: {
    total: number
    pending: number
    published: number
    archived: number
    new_7d: number
  }
}

// 用户统计响应
export interface UserStatsResponse {
  nodes_count: number
  likes_count: number
  comments_count: number
  branches_count: number
}

// 故事册节点统计
export interface StoryBookNodeStats {
  total_nodes: number
  published_nodes: number
  pending_nodes: number
  archived_nodes: number
}

// 节点树统计
export interface NodeTreeStats {
  root_nodes_count: number
  leaf_nodes_count: number
  branch_nodes_count: number
  max_depth: number
}

// 按照 cline.md 规范，所有 API 响应都应遵循统一格式
export interface ApiResponse<T = unknown> {
  data?: T
  detail?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

// API 错误响应类型（在 api.ts 中定义，这里提供类型引用）
// import { ApiErrorResponse } from '@/types/api'
export type ApiErrorResponse = {
  detail: string
} | {
  detail: Array<{ loc: (string | number)[]; msg: string; type: string }>
}

// 管理员节点统计
export interface AdminNodeStatsResponse {
  pending_count: number
  published_count: number
  archived_count: number
}

// 用户节点统计响应
export interface UserNodeStatsResponse {
  published_nodes_count: number
  pending_nodes_count: number
  archived_nodes_count: number
}

// 故事册节点总数（用于 StoryBookDetailPage）
export interface StoryBookNodesCountResponse {
  nodes_count: number
}

// 节点路径类型（用于 StoryNodePage）
export interface NodePathResponse extends StoryNodeRead {
  depth: number
}

// 树状节点响应（用于 StoryBookDetailPage）
export interface StoryTreeResponse extends StoryNodeTreeItem {}

// 故事册统计响应
export interface StoryBookStatsResponse {
  total_books: number
  active_books: number
  pending_books: number
  writing_books: number
  showcase_books: number
}
