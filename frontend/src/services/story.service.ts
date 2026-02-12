import api from './api'
import type {
  CreateBookRequest,
  UpdateBookRequest,
  StoryBook,
  CreateNodeRequest,
  UpdateNodeRequest,
  StoryNodeTreeItem,
  StoryNodeRead,
  StoryNodeListItem,
  GetStoryTreeParams,
  GetUserNodesParams,
  MessageResponse,
} from '@/types'

// ==================== 故事书/活动相关 ====================

// 获取活动列表
export const getBooks = (params?: { skip?: number; limit?: number }) => {
  return api.get<StoryBook[]>('/story/books', { params })
}

// 创建活动 [Admin]
export const createBook = (data: CreateBookRequest) => {
  return api.post<StoryBook>('/story/books', data)
}

// 更新活动 [Admin]
export const updateBook = (bookId: number, data: UpdateBookRequest) => {
  return api.patch<StoryBook>(`/story/books/${bookId}`, null, { params: data })
}

// ==================== 故事节点相关 ====================

// 获取故事树结构
export const getStoryTree = (params: GetStoryTreeParams) => {
  return api.get<StoryNodeTreeItem[]>('/story/tree', { params })
}

// 获取节点详情
export const getNodeDetail = (nodeId: number) => {
  return api.get<StoryNodeRead>(`/story/node/${nodeId}`)
}

// 获取阅读路径（溯源）
export const getNodePath = (nodeId: number) => {
  return api.get<StoryNodeRead[]>(`/story/node/${nodeId}/path`)
}

// 创建节点（续写）
export const createNode = (data: CreateNodeRequest) => {
  return api.post<StoryNodeListItem>('/story/node', data)
}

// 更新节点
export const updateNode = (nodeId: number, data: UpdateNodeRequest) => {
  return api.patch<StoryNodeRead>(`/story/node/${nodeId}`, null, { params: data })
}

// 删除节点
export const deleteNode = (nodeId: number) => {
  return api.delete<MessageResponse>(`/story/node/${nodeId}`)
}

// 获取用户的创作列表
export const getUserNodes = (userId: number, params?: GetUserNodesParams) => {
  return api.get<StoryNodeListItem[]>(`/story/user/${userId}/nodes`, { params })
}