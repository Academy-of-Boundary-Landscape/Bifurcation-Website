import api from './api'
import type { CreateCommentRequest, Comment, Notification, MessageResponse } from '@/types'

// ==================== 互动相关 ====================

// 点赞/取消点赞
export const toggleLike = (nodeId: number) => {
  return api.post<{ status: string; action: string; likes_count: number }>(`/interaction/node/${nodeId}/like`)
}

// 获取评论列表
export const getComments = (nodeId: number, params?: { skip?: number; limit?: number }) => {
  return api.get<Comment[]>(`/interaction/node/${nodeId}/comments`, { params })
}

// 发表评论
export const createComment = (nodeId: number, data: CreateCommentRequest) => {
  return api.post<Comment>(`/interaction/node/${nodeId}/comment`, data)
}

// ==================== 通知相关 ====================

// 获取通知列表
export const getNotifications = (params?: { skip?: number; limit?: number }) => {
  return api.get<Notification[]>('/interaction/notifications', { params })
}

// 一键已读
export const markNotificationsRead = () => {
  return api.put<MessageResponse>('/interaction/notifications/read')
}