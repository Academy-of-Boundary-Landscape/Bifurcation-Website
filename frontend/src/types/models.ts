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

// 用户节点统计响应
export interface UserNodeStatsResponse {
  published_nodes_count: number
  pending_nodes_count: number
  archived_nodes_count: number
}
