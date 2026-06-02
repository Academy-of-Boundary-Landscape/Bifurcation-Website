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

// 统一错误响应类型
export type ApiErrorResponse = ErrorResponse | ValidationErrorResponse

// Token 响应
export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface SsoLoginUrlResponse {
  authorize_url: string
  state: string
}

export interface SsoExchangeResponse extends TokenResponse {
  redirect_to: string
  is_new_user: boolean
}
