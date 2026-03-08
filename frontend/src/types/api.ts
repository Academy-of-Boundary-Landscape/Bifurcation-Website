// API 响应基础类型
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

// 错误响应
export interface ErrorResponse {
  detail: string
}

export interface ValidationErrorResponse {
  detail: ValidationErrorItem[]
}

export interface ValidationErrorItem {
  loc: (string | number)[]
  msg: string
  type: string
}

// Token 响应
export interface TokenResponse {
  access_token: string
  token_type: string
}

// 消息响应
export interface MessageResponse {
  detail: string
}

// 上传响应
export interface UploadResponse {
  url: string
}