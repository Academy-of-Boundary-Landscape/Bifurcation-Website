import { get, patch } from '@/services/http'
import type { AdminDashboardStats, NodeAuditRequest, StoryNodeRead, User, UserRole } from '@/types/models'

export async function fetchAdminStats() {
  return get<AdminDashboardStats>('/admin/stats')
}

export async function fetchAdminUsers(params?: {
  skip?: number
  limit?: number
  role?: UserRole
  is_active?: boolean
  keyword?: string
}) {
  const queryParams = new URLSearchParams()

  if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
  if (params?.role) queryParams.append('role', params.role)
  if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active))
  if (params?.keyword) queryParams.append('keyword', params.keyword)

  const suffix = queryParams.toString()
  return get<User[]>(suffix ? `/admin/users?${suffix}` : '/admin/users')
}

export async function updateAdminUser(
  userId: number,
  payload: {
    role?: UserRole
    is_active?: boolean
    username?: string | null
    bio?: string | null
    avatar?: string | null
  }
) {
  return patch<User>(`/admin/users/${userId}`, payload)
}

export async function fetchAdminNodes(params?: {
  skip?: number
  limit?: number
  status?: 'pending' | 'published' | 'archived'
  book_id?: number
  author_id?: number
  keyword?: string
}) {
  const queryParams = new URLSearchParams()

  if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
  if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
  if (params?.status) queryParams.append('status', params.status)
  if (params?.book_id !== undefined) queryParams.append('book_id', params.book_id.toString())
  if (params?.author_id !== undefined) queryParams.append('author_id', params.author_id.toString())
  if (params?.keyword) queryParams.append('keyword', params.keyword)

  const suffix = queryParams.toString()
  return get<StoryNodeRead[]>(suffix ? `/admin/nodes?${suffix}` : '/admin/nodes')
}

export async function auditPendingNode(nodeId: number, payload: NodeAuditRequest) {
  return patch<StoryNodeRead>(`/admin/nodes/${nodeId}/audit`, payload)
}
