import { getList } from '@/services/http'
import type { StoryNode } from '@/types/models'

// 列表返回 { items, total }，total 来自后端 X-Total-Count（真实总数，不受 limit 截断）
export async function fetchFeaturedNodes(params?: { limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.limit !== undefined) queryParams.append('limit', String(params.limit))

  return getList<StoryNode>(`/discovery/featured?${queryParams}`)
}

export async function fetchLatestFeed(params?: { bookId?: number; skip?: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.bookId) queryParams.append('book_id', String(params.bookId))
  if (params?.skip !== undefined) queryParams.append('skip', String(params.skip))
  if (params?.limit !== undefined) queryParams.append('limit', String(params.limit))

  return getList<StoryNode>(`/discovery/feed?${queryParams}`)
}

export async function fetchTrendingNodes(params?: { days?: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params?.days !== undefined) queryParams.append('days', String(params.days))
  if (params?.limit !== undefined) queryParams.append('limit', String(params.limit))

  return getList<StoryNode>(`/discovery/trending?${queryParams}`)
}

export async function searchDiscoveryNodes(params: { q: string; limit?: number }) {
  const queryParams = new URLSearchParams()
  queryParams.append('q', params.q)
  if (params.limit !== undefined) queryParams.append('limit', String(params.limit))

  return getList<StoryNode>(`/discovery/search?${queryParams}`)
}
