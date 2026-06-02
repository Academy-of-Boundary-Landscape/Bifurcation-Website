import { get, getList, post, patch, del } from '@/services/http'
import type {
  StoryBook,
  StoryBookCreate,
  StoryNode,
  StoryNodeRead,
  StoryNodeCreate,
  StoryNodeTreeItem,
  UserNodeStatsResponse,
} from '@/types/models'

// 故事册相关 API
export async function fetchBooks(params?: { phase?: string }) {
  const queryParams = new URLSearchParams()
  if (params?.phase) queryParams.append('phase', params.phase)

  // 返回 { items, total }，total 为 X-Total-Count 真实活动总数
  return getList<StoryBook>(`/story/books?${queryParams}`)
}

export async function fetchBook(bookId: number) {
  return get<StoryBook>(`/story/books/${bookId}`)
}

export async function createBook(payload: StoryBookCreate) {
  return post<StoryBook>('/story/books', payload)
}

export async function updateBook(bookId: number, payload: Partial<StoryBook>) {
  return patch<StoryBook>(`/story/books/${bookId}`, payload)
}

// 故事节点相关 API
export async function fetchStoryTree(bookId: number) {
  return get<StoryNodeTreeItem[]>(`/story/tree?book_id=${bookId}`)
}

export async function fetchNodePath(nodeId: number) {
  return get<StoryNode[]>(`/story/node/${nodeId}/path`)
}

export async function fetchNodeDetail(nodeId: number) {
  return get<StoryNodeRead>(`/story/node/${nodeId}`)
}

export async function fetchNodeLineage(nodeId: number) {
  return get<StoryNodeRead[]>(`/story/node/${nodeId}/lineage`)
}

export async function fetchNodeChildren(nodeId: number, params?: { limit?: number }) {
  const queryParams = new URLSearchParams()
  queryParams.append('parent_id', nodeId.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())

  return get<StoryNode[]>(`/story/node?${queryParams}`)
}

export async function createStoryNode(payload: StoryNodeCreate) {
  return post<StoryNodeRead>('/story/node', payload)
}

export async function updateStoryNode(nodeId: number, payload: Partial<StoryNodeCreate>) {
  return patch<StoryNodeRead>(`/story/node/${nodeId}`, payload)
}

export async function deleteStoryNode(nodeId: number) {
  return del<{ detail: string }>(`/story/node/${nodeId}`)
}

// 用户节点统计
export async function fetchUserNodeStats(userId: number) {
  return get<UserNodeStatsResponse>(`/story/user/${userId}/stats`)
}
