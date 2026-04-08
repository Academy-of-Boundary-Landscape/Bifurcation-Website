import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import type {
  CommentCreate,
} from '@/types/models'
import {
  toggleLike,
  fetchNodeComments,
  createComment,
  deleteComment,
  fetchNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  fetchUnreadCount
} from './api'
import { queryKeys } from '@/features/queryKeys'

// 点赞相关 Queries
export function useToggleLikeMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ nodeId, bookId }: { nodeId: number; bookId?: number }) => toggleLike(nodeId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.storyNode(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.nodeComments(variables.nodeId) })

      if (variables.bookId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.storyTree(variables.bookId) })
      } else {
        queryClient.invalidateQueries({ queryKey: queryKeys.storyTreesRoot() })
      }
    }
  })
}

// 评论相关 Queries
export function useNodeCommentsQuery(nodeId: MaybeRefOrGetter<number>, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: computed(() => queryKeys.nodeComments(toValue(nodeId), params)),
    queryFn: () => fetchNodeComments(toValue(nodeId), params),
    enabled: computed(() => !!toValue(nodeId)),
  })
}

export function useCreateCommentMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: number; payload: CommentCreate }) => 
      createComment(nodeId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.nodeComments(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyNode(variables.nodeId) })
    }
  })
}

export function useDeleteCommentMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ commentId }: { commentId: number; nodeId: number }) => deleteComment(commentId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.nodeComments(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyNode(variables.nodeId) })
    }
  })
}

// 通知相关 Queries
export function useNotificationsQuery(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.notifications(params),
    queryFn: () => fetchNotifications(params),
  })
}

export function useUnreadCountQuery() {
  return useQuery({
    queryKey: queryKeys.unreadCount(),
    queryFn: () => fetchUnreadCount(),
  })
}

export function useMarkNotificationAsReadMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ notificationId }: { notificationId: number }) => markNotificationAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationsRoot() })
      queryClient.invalidateQueries({ queryKey: queryKeys.unreadCount() })
    }
  })
}

export function useMarkAllNotificationsAsReadMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => markAllNotificationsAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationsRoot() })
      queryClient.invalidateQueries({ queryKey: queryKeys.unreadCount() })
    }
  })
}
