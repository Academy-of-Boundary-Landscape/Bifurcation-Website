import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import type { NodeAuditRequest, NodeStatus, UserRole } from '@/types/models'
import { auditPendingNode, fetchAdminNodes, fetchAdminStats, fetchAdminUsers, updateAdminUser } from './api'
import { queryKeys } from '@/features/queryKeys'

export function useAdminStatsQuery() {
  return useQuery({
    queryKey: queryKeys.adminStats(),
    queryFn: () => fetchAdminStats(),
  })
}

export function useAdminUsersQuery(
  params?: MaybeRefOrGetter<{
    skip?: number
    limit?: number
    role?: UserRole
    is_active?: boolean
    keyword?: string
  }>
) {
  return useQuery({
    queryKey: computed(() => queryKeys.adminUsers(toValue(params))),
    queryFn: () => fetchAdminUsers(toValue(params)),
  })
}

export function useAdminNodesQuery(
  params?: MaybeRefOrGetter<{
    skip?: number
    limit?: number
    status?: NodeStatus
    book_id?: number
    author_id?: number
    keyword?: string
  }>
) {
  return useQuery({
    queryKey: computed(() => queryKeys.adminNodes(toValue(params))),
    queryFn: () => fetchAdminNodes(toValue(params)),
  })
}

export function useAdminUpdateUserMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: number
      payload: {
        role?: UserRole
        is_active?: boolean
        username?: string | null
        bio?: string | null
        avatar?: string | null
      }
    }) => updateAdminUser(userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminUsersRoot() })
      queryClient.invalidateQueries({ queryKey: queryKeys.adminStats() })
    },
  })
}

export function useAuditStoryNodeMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: number; payload: NodeAuditRequest }) =>
      auditPendingNode(nodeId, payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.storyNode(variables.nodeId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.storyTree(data.book_id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.pendingNodesRoot() })
      queryClient.invalidateQueries({ queryKey: queryKeys.adminNodesRoot() })
    },
  })
}
