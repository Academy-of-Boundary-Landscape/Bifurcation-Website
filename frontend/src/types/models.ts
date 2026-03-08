// 用户角色
export type UserRole = 'admin' | 'writer' | 'banned'

// 节点状态
export type NodeStatus = 'pending' | 'published' | 'locked' | 'rejected'

// 用户
export interface User {
  id: number
  email: string
  username: string
  role: UserRole
  is_active: boolean
  is_verified: boolean
  bio: string | null
  avatar: string | null
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
  created_at: string
}

export interface StoryBookCreate {
  title: string
  description?: string | null
  cover_image?: string | null
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
  book_id: number
  author: AuthorInfo
  title: string | null
  summary: string | null
  branch_name: string | null
  status: NodeStatus
  depth: number
  likes_count: number
  created_at: string
}

export interface StoryNodeRead extends StoryNode {
  content: string
}

export interface StoryNodeCreate {
  book_id: number
  parent_id?: number | null
  title?: string | null
  content: string
  branch_name?: string | null
}

export interface StoryNodeTreeItem extends StoryNode {
  children: StoryNodeTreeItem[]
}

// 评论
export interface Comment {
  id: number
  content: string
  created_at: string
  user: AuthorInfo
}

export interface CommentCreate {
  content: string
}

// 通知
export interface Notification {
  id: number
  type: string
  sender: AuthorInfo
  target_id: number
  is_read: boolean
  created_at: string
}

// 点赞
export interface LikeToggleResponse {
  status: string
  action: 'like' | 'unlike'
  likes_count: number
}