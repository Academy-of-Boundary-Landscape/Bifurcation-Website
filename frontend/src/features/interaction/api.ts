import { get, post, put, patch, del } from '@/services/http'
import type {
  Comment,
  CommentCreate,
  Notification,
  LikeToggleResponse
} from '@/types/models'

// 点赞相关 API
export async function toggleLike(nodeId: number) {
  return post<LikeToggleResponse>(`/interaction/node/${nodeId}/like`)
}

// 评论相关 API
export async function fetchNodeComments(nodeId: number, params?: { skip?: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
  
  return get<Comment[]>(`/interaction/node/${nodeId}/comments?${queryParams}`)
}

export async function createComment(nodeId: number, payload: CommentCreate) {
  return post<Comment>(`/interaction/node/${nodeId}/comment`, payload)
}

export async function deleteComment(commentId: number) {
  return del<{ detail: string }>(`/interaction/comment/${commentId}`)
}

// 通知相关 API
export async function fetchNotifications(params?: { skip?: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
  const qs = queryParams.toString()
  return get<Notification[]>(`/interaction/notifications${qs ? `?${qs}` : ''}`)
}

export async function markAllNotificationsAsRead() {
  return put<{ detail: string }>(`/interaction/notifications/read`)
}

export async function markNotificationAsRead(notificationId: number) {
  return put<{ detail: string }>(`/interaction/notifications/${notificationId}/read`)
}

export async function fetchUnreadCount() {
  return get<{ unread_count: number }>(`/interaction/notifications/unread-count`)
}
