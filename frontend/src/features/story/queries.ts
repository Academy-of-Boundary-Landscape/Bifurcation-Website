import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import type {
  BookPhase,
  StoryBookCreate,
  StoryNodeCreate,
} from '@/types/models'
import {
  fetchBooks,
  fetchBook,
  createBook,
  updateBook,
  fetchStoryTree,
  fetchNodePath,
  fetchNodeDetail,
  fetchNodeLineage,
  fetchNodeChildren,
  createStoryNode,
  deleteStoryNode,
} from './api'
import { queryKeys } from '@/features/queryKeys'

// 故事册相关 Queries
export function useBooksQuery(params?: { phase?: string }) {
  return useQuery({
    queryKey: queryKeys.books(params),
    queryFn: () => fetchBooks(params),
  })
}

export function useBookQuery(bookId: MaybeRefOrGetter<number>) {
  return useQuery({
    queryKey: computed(() => queryKeys.book(toValue(bookId))),
    queryFn: () => fetchBook(toValue(bookId)),
    enabled: computed(() => !!toValue(bookId)),
  })
}

// 故事树相关 Queries
export function useStoryTreeQuery(bookId: MaybeRefOrGetter<number>) {
  return useQuery({
    queryKey: computed(() => queryKeys.storyTree(toValue(bookId))),
    queryFn: () => fetchStoryTree(toValue(bookId)),
    enabled: computed(() => !!toValue(bookId)),
  })
}

// 节点路径相关 Queries
export function useNodePathQuery(nodeId: MaybeRefOrGetter<number>) {
  return useQuery({
    queryKey: computed(() => queryKeys.nodePath(toValue(nodeId))),
    queryFn: () => fetchNodePath(toValue(nodeId)),
    enabled: computed(() => !!toValue(nodeId)),
  })
}

// 节点详情相关 Queries
export function useNodeDetailQuery(nodeId: MaybeRefOrGetter<number>) {
  return useQuery({
    queryKey: computed(() => queryKeys.storyNode(toValue(nodeId))),
    queryFn: () => fetchNodeDetail(toValue(nodeId)),
    enabled: computed(() => !!toValue(nodeId)),
  })
}

export function useNodeLineageQuery(nodeId: MaybeRefOrGetter<number>) {
  return useQuery({
    queryKey: computed(() => queryKeys.storyLineage(toValue(nodeId))),
    queryFn: () => fetchNodeLineage(toValue(nodeId)),
    enabled: computed(() => !!toValue(nodeId)),
  })
}

export function useNodeChildrenQuery(nodeId: MaybeRefOrGetter<number>, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: computed(() => queryKeys.nodeChildren(toValue(nodeId))),
    queryFn: () => fetchNodeChildren(toValue(nodeId), params),
    enabled: computed(() => !!toValue(nodeId)),
  })
}

// Mutation Hooks
export function useCreateBookMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (payload: StoryBookCreate) => createBook(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.books() })
    }
  })
}

export function useUpdateBookMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ bookId, payload }: { bookId: number; payload: Partial<StoryBookCreate> & { phase?: BookPhase; is_active?: boolean } }) =>
      updateBook(bookId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.book(data.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.booksRoot() })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyTree(data.id) })
    }
  })
}

export function useCreateStoryNodeMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (payload: StoryNodeCreate) => createStoryNode(payload),
    onSuccess: (data) => {
      // 更新树和节点详情缓存
      queryClient.invalidateQueries({ queryKey: queryKeys.storyTree(data.book_id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyNode(data.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.nodePath(data.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.booksRoot() })
    }
  })
}

export function useDeleteStoryNodeMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ nodeId }: { nodeId: number }) => deleteStoryNode(nodeId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.storyNode(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.nodePath(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.nodeChildren(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyLineage(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.booksRoot() })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyTreesRoot() })
    }
  })
}
