import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { useAuthStore } from '@/stores/auth'
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

// 评论列表的无限滚动版本：每次拉一页，超过当前页就用 fetchNextPage 续拉
const COMMENTS_PAGE_SIZE = 20
export function useInfiniteNodeCommentsQuery(nodeId: MaybeRefOrGetter<number>) {
  return useInfiniteQuery({
    queryKey: computed(() => queryKeys.nodeComments(toValue(nodeId))),
    queryFn: ({ pageParam }) => fetchNodeComments(toValue(nodeId), {
      skip: pageParam as number,
      limit: COMMENTS_PAGE_SIZE,
    }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < COMMENTS_PAGE_SIZE) return undefined
      return allPages.length * COMMENTS_PAGE_SIZE
    },
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

const NOTIFICATIONS_PAGE_SIZE = 20

// 通知相关 Queries
export function useInfiniteNotificationsQuery() {
  return useInfiniteQuery({
    queryKey: queryKeys.notificationsRoot(),
    queryFn: ({ pageParam }) => fetchNotifications({ skip: pageParam as number, limit: NOTIFICATIONS_PAGE_SIZE }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.items.length < NOTIFICATIONS_PAGE_SIZE) return undefined
      return allPages.length * NOTIFICATIONS_PAGE_SIZE
    },
  })
}

export function useUnreadCountQuery() {
  const authStore = useAuthStore()
  return useQuery({
    queryKey: queryKeys.unreadCount(),
    queryFn: () => fetchUnreadCount(),
    enabled: computed(() => authStore.isAuthenticated),
    refetchInterval: 60_000,
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
