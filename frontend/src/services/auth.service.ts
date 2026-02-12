import api from './api'
import type {
  SendCodeRequest,
  EmailVerifyRequest,
  RegisterRequest,
  RegisterResponse,
  LoginFormData,
  TokenResponse,
  UpdateProfileRequest,
  ResetPasswordRequest,
  MessageResponse,
  UserProfile,
} from '@/types'

// 发送激活验证码
export const sendActivationCode = (data: SendCodeRequest) => {
  return api.post<MessageResponse>('/auth/send-code-for-activation', data)
}

// 验证邮箱（激活账号）
export const verifyEmailForActivation = (data: EmailVerifyRequest) => {
  return api.post<MessageResponse>('/auth/verify-email-for-activation', data)
}

// 用户注册
export const register = (data: RegisterRequest) => {
  return api.post<RegisterResponse>('/auth/register', data)
}

// 用户登录（使用表单数据格式）
export const login = (data: LoginFormData) => {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)
  if (data.grant_type) formData.append('grant_type', data.grant_type)
  if (data.scope) formData.append('scope', data.scope)
  if (data.client_id) formData.append('client_id', data.client_id)
  if (data.client_secret) formData.append('client_secret', data.client_secret)

  return api.post<TokenResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

// 获取当前用户信息
export const getMe = () => {
  return api.get<UserProfile>('/auth/me')
}

// 更新个人资料
export const updateMe = (data: UpdateProfileRequest) => {
  return api.patch<UserProfile>('/auth/me', data)
}

// 发送重置密码验证码
export const sendPasswordResetCode = (data: EmailVerifyRequest) => {
  return api.post<MessageResponse>('/auth/send-code-for-password-reset', data)
}

// 重置密码
export const resetPassword = (data: ResetPasswordRequest) => {
  return api.post<MessageResponse>('/auth/reset-password', data)
}