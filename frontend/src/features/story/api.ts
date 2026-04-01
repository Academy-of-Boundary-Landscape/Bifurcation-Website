import { get, post, put, patch, del } from '@/services/http'
import type {
  StoryBook,
  StoryBookCreate,
  StoryNode,
  StoryNodeRead,
  StoryNodeCreate,
  StoryNodeTreeItem,
  Comment,
  CommentCreate,
  NodeAuditRequest,
  UserNodeStatsResponse,
  UserNotificationsSummary,
} from '@/types/models'

// 故事册相关 API
export async function fetchBooks(params?: { phase?: string }) {
  const queryParams = new URLSearchParams()
  if (params?.phase) queryParams.append('phase', params.phase)
  
  return get<StoryBook[]>(`/api/v1/story/books?${queryParams}`)
}

export async function createBook(payload: StoryBookCreate) {
  return post<StoryBook>('/api/v1/story/books', payload)
}

export async function updateBook(bookId: number, payload: Partial<StoryBook>) {
  return patch<StoryBook>(`/api/v1/story/books/${bookId}`, payload)
}

// 故事节点相关 API
export async function fetchStoryTree(bookId: number) {
  return get<StoryNodeTreeItem[]>(`/api/v1/story/tree?book_id=${bookId}`)
}

export async function fetchNodePath(nodeId: number) {
  return get<StoryNode[]>(`/api/v1/story/node/${nodeId}/path`)
}

export async function fetchNodeDetail(nodeId: number) {
  return get<StoryNodeRead>(`/api/v1/story/node/${nodeId}`)
}

export async function fetchNodeLineage(nodeId: number) {
  return get<StoryNodeRead[]>(`/api/v1/story/node/${nodeId}/lineage`)
}

export async function createStoryNode(payload: StoryNodeCreate) {
  return post<StoryNodeRead>('/api/v1/story/node', payload)
}

export async function updateStoryNode(nodeId: number, payload: Partial<StoryNodeCreate>) {
  return patch<StoryNodeRead>(`/api/v1/story/node/${nodeId}`, payload)
}

export async function deleteStoryNode(nodeId: number) {
  return del<{ detail: string }>(`/api/v1/story/node/${nodeId}`)
}

// 审核相关 API
export async function getPendingNodes(params?: { skip?: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
  
  return get<StoryNodeTreeItem[]>(`/api/v1/admin/nodes/pending?${queryParams}`)
}

export async function auditStoryNode(nodeId: number, payload: NodeAuditRequest) {
  return patch<StoryNodeRead>(`/api/v1/admin/nodes/${nodeId}/audit`, payload)
}

// 评论相关 API
export async function fetchNodeComments(nodeId: number, params?: { skip?: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
  
  return get<Comment[]>(`/api/v1/interaction/node/${nodeId}/comments?${queryParams}`)
}

export async function createComment(nodeId: number, payload: CommentCreate) {
  return post<Comment>(`/api/v1/interaction/node/${nodeId}/comment`, payload)
}

export async function deleteComment(commentId: number) {
  return del<{ detail: string }>(`/api/v1/interaction/comment/${commentId}`)
}

// 用户节点统计
export async function fetchUserNodeStats(userId: number) {
  return get<UserNodeStatsResponse>(`/story/user/${userId}/stats`)
}

// 用户通知统计
export async function fetchUserNotificationsSummary(userId: number) {
  return get<UserNotificationsSummary>(`/interaction/user/${userId}/notifications/summary`)
}
