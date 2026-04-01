import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type {
  Comment,
  CommentCreate,
  Notification,
  LikeToggleResponse
} from '@/types/models'
import {
  toggleLike,
  fetchNodeComments,
  createComment,
  deleteComment,
  fetchNotifications,
  markAllNotificationsAsRead,
  fetchUnreadCount
} from './api'

// 点赞相关 Queries
export function useToggleLikeMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (nodeId: number) => toggleLike(nodeId),
    onSuccess: (data, nodeId) => {
      // 更新节点详情缓存
      queryClient.invalidateQueries({ queryKey: ['node-detail', nodeId] })
      queryClient.invalidateQueries({ queryKey: ['story-tree'] })
      queryClient.invalidateQueries({ queryKey: ['node-comments', nodeId] })
    }
  })
}

// 评论相关 Queries
export function useNodeCommentsQuery(nodeId: number, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['node-comments', nodeId, params],
    queryFn: () => fetchNodeComments(nodeId, params),
    enabled: !!nodeId,
  })
}

export function useCreateCommentMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: number; payload: CommentCreate }) => 
      createComment(nodeId, payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['node-comments', variables.nodeId] })
      queryClient.invalidateQueries({ queryKey: ['node-detail', variables.nodeId] })
      queryClient.invalidateQueries({ queryKey: ['story-tree'] })
    }
  })
}

export function useDeleteCommentMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (commentId: number) => deleteComment(commentId),
    onSuccess: (_, commentId) => {
      // 这里需要获取节点 ID，简化处理
      queryClient.invalidateQueries({ queryKey: ['node-comments'] })
      queryClient.invalidateQueries({ queryKey: ['story-tree'] })
    }
  })
}

// 通知相关 Queries
export function useNotificationsQuery(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['notifications', params],
    queryFn: () => fetchNotifications(params),
  })
}

export function useUnreadCountQuery() {
  return useQuery({
    queryKey: ['unread-count'],
    queryFn: () => fetchUnreadCount(),
  })
}

export function useMarkAllNotificationsAsReadMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => markAllNotificationsAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
    }
  })
}
