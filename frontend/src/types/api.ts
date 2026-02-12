// API 响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 简单响应（后端大多返回这种格式）
export interface MessageResponse {
  detail: string
}

// 错误响应
export interface ErrorResponse {
  detail: string
}

// 分页参数
export interface PaginationParams {
  skip?: number
  limit?: number
}

// ==================== 认证相关 ====================

// 发送验证码请求
export interface SendCodeRequest {
  email: string
}

// 邮箱验证请求（用于激活或重置密码）
export interface EmailVerifyRequest {
  email: string
  code: string
}

// 用户注册请求
export interface RegisterRequest {
  email: string
  username: string
  password: string
}

// 用户注册响应
export interface RegisterResponse {
  email: string
  username: string
  id: number
  role: string
  is_active: boolean
  is_verified: boolean
}

// 登录请求（表单数据格式）
export interface LoginFormData {
  username: string
  password: string
  grant_type?: string
  scope?: string
  client_id?: string
  client_secret?: string
}

// 登录响应（Token）
export interface TokenResponse {
  access_token: string
  token_type: string
}

// 修改个人资料请求
export interface UpdateProfileRequest {
  username?: string
  bio?: string
  avatar?: string
}

// 重置密码请求
export interface ResetPasswordRequest {
  email: string
  code: string
  new_password: string
}

// ==================== 故事相关 ====================

// 创建活动请求
export interface CreateBookRequest {
  title: string
  description?: string | null
  cover_image?: string | null
}

// 更新活动请求
export interface UpdateBookRequest {
  title?: string | null
  description?: string | null
  cover_image?: string | null
  is_active?: boolean | null
}

// 创建节点请求
export interface CreateNodeRequest {
  book_id: number
  parent_id?: number | null
  title?: string | null
  content: string
  branch_name?: string | null
}

// 更新节点请求
export interface UpdateNodeRequest {
  title?: string | null
  content?: string | null
  branch_name?: string | null
}

// 获取故事树参数
export interface GetStoryTreeParams {
  book_id: number
}

// ==================== 互动相关 ====================

// 创建评论请求
export interface CreateCommentRequest {
  content: string
}

// ==================== 发现相关 ====================

// 获取 Feed 参数
export interface GetFeedParams {
  book_id?: number | null
  skip?: number
  limit?: number
}

// 获取热门节点参数
export interface GetTrendingParams {
  days?: number
  limit?: number
}

// 搜索节点参数
export interface SearchParams {
  q: string
  limit?: number
}

// ==================== 管理员相关 ====================

// 审核节点请求
export interface AuditNodeRequest {
  status: 'published' | 'rejected'
}

// 管理员更新用户请求
export interface AdminUpdateUserRequest {
  role?: 'admin' | 'writer' | 'banned'
  is_active?: boolean
  username?: string
  bio?: string
  avatar?: string
}

// 获取待审核节点参数
export interface GetPendingNodesParams {
  skip?: number
  limit?: number
}

// 获取用户创作列表参数
export interface GetUserNodesParams {
  status?: 'pending' | 'published' | 'locked' | 'rejected'
  skip?: number
  limit?: number
}