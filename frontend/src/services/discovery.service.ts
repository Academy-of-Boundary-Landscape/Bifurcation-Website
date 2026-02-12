import api from './api'
import type { StoryNodeListItem, GetFeedParams, GetTrendingParams, SearchParams } from '@/types'

// ==================== 发现相关 ====================

// 获取最新动态 Feed
export const getFeed = (params?: GetFeedParams) => {
  return api.get<StoryNodeListItem[]>('/discovery/feed', { params })
}

// 获取热门榜单
export const getTrending = (params?: GetTrendingParams) => {
  return api.get<StoryNodeListItem[]>('/discovery/trending', { params })
}

// 搜索
export const search = (params: SearchParams) => {
  return api.get<StoryNodeListItem[]>('/discovery/search', { params })
}