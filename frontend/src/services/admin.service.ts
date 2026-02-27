import api from './api'
import type {
  AuditNodeRequest,
  StoryNodeTreeItem,
  AdminUpdateUserRequest,
  GetPendingNodesParams,
  GetAdminUsersParams,
  AdminDashboardStats,
  User,
  MessageResponse,
} from '@/types'

// ==================== 管理员相关 ====================

// 获取待审核节点列表
export const getPendingNodes = (params?: GetPendingNodesParams) => {
  return api.get<StoryNodeTreeItem[]>('/admin/nodes/pending', { params })
}

// 审核节点
export const auditNode = (nodeId: number, data: AuditNodeRequest) => {
  return api.patch<StoryNodeTreeItem>(`/admin/nodes/${nodeId}/audit`, data)
}

// 管理员更新用户（封禁、改角色）
export const adminUpdateUser = (userId: number, data: AdminUpdateUserRequest) => {
  return api.patch(`/admin/users/${userId}`, data)
}

// 管理员用户列表
export const getAdminUsers = (params?: GetAdminUsersParams) => {
  return api.get<User[]>('/admin/users', { params })
}

// 管理员仪表盘统计
export const getAdminStats = () => {
  return api.get<AdminDashboardStats>('/admin/stats')
}