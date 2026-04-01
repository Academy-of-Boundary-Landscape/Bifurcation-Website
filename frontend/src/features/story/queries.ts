import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type {
  StoryBook,
  StoryBookCreate,
  StoryNode,
  StoryNodeRead,
  StoryNodeCreate,
  StoryNodeTreeItem,
  Comment,
  CommentCreate,
  NodeAuditRequest
} from '@/types/models'
import {
  fetchBooks,
  createBook,
  updateBook,
  fetchStoryTree,
  fetchNodePath,
  fetchNodeDetail,
  createStoryNode,
  updateStoryNode,
  deleteStoryNode,
  auditStoryNode,
  fetchNodeComments,
  createComment,
  deleteComment,
  getPendingNodes
} from './api'

// 故事册相关 Queries
export function useBooksQuery(params?: { phase?: string }) {
  return useQuery({
    queryKey: ['books', params],
    queryFn: () => fetchBooks(params),
  })
}

export function useBookQuery(bookId: number) {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: () => fetchBooks().then(books => books.find(b => b.id === bookId)),
    enabled: !!bookId,
  })
}

// 故事树相关 Queries
export function useStoryTreeQuery(bookId: number) {
  return useQuery({
    queryKey: ['story-tree', bookId],
    queryFn: () => fetchStoryTree(bookId),
    enabled: !!bookId,
  })
}

// 节点路径相关 Queries
export function useNodePathQuery(nodeId: number) {
  return useQuery({
    queryKey: ['node-path', nodeId],
    queryFn: () => fetchNodePath(nodeId),
    enabled: !!nodeId,
  })
}

// 节点详情相关 Queries
export function useNodeDetailQuery(nodeId: number) {
  return useQuery({
    queryKey: ['node-detail', nodeId],
    queryFn: () => fetchNodeDetail(nodeId),
    enabled: !!nodeId,
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

// Pending nodes related Queries
export function usePendingNodesQuery(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['pending-nodes', params],
    queryFn: () => getPendingNodes(params),
  })
}

// Mutation Hooks
export function useCreateBookMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (payload: StoryBookCreate) => createBook(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] })
    }
  })
}

export function useCreateStoryNodeMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (payload: StoryNodeCreate) => createStoryNode(payload),
    onSuccess: (data) => {
      // 更新树和节点详情缓存
      queryClient.invalidateQueries({ queryKey: ['story-tree', data.book_id] })
      queryClient.invalidateQueries({ queryKey: ['node-detail', data.id] })
      queryClient.invalidateQueries({ queryKey: ['node-path', data.id] })
      queryClient.invalidateQueries({ queryKey: ['books'] })
    }
  })
}

export function useAuditStoryNodeMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: number; payload: NodeAuditRequest }) => 
      auditStoryNode(nodeId, payload),
    onSuccess: (data, variables) => {
      // 更新节点详情缓存
      queryClient.invalidateQueries({ queryKey: ['node-detail', variables.nodeId] })
      queryClient.invalidateQueries({ queryKey: ['story-tree', data.book_id] })
      queryClient.invalidateQueries({ queryKey: ['pending-nodes'] })
    }
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
    }
  })
}

export function useDeleteCommentMutation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (commentId: number) => deleteComment(commentId),
    onSuccess: (_, commentId) => {
      // 需要获取节点 ID 来更新缓存
      // 这里简化处理，实际项目中需要更精确的缓存管理
      queryClient.invalidateQueries({ queryKey: ['node-comments'] })
    }
  })
}