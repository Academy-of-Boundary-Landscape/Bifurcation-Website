import api from './api'
import type { UserProfile } from '@/types'

// 获取用户资料（公开）
export const getUserProfile = (userId: number) => {
  return api.get<UserProfile>(`/users/${userId}`)
}