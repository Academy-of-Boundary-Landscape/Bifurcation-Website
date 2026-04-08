import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { fetchMyProfile, fetchUserNodes, updateMyProfile, uploadUserAvatar } from './api'
import { queryKeys } from '@/features/queryKeys'

export function useMyProfileQuery() {
  return useQuery({
    queryKey: queryKeys.userProfile(),
    queryFn: () => fetchMyProfile(),
  })
}

export function useUserNodesQuery(
  params: MaybeRefOrGetter<{
    authorId?: number
    limit?: number
  }>
) {
  return useQuery({
    queryKey: computed(() => queryKeys.userNodes(toValue(params))),
    queryFn: () => fetchUserNodes({ authorId: toValue(params).authorId!, limit: toValue(params).limit }),
    enabled: computed(() => !!toValue(params).authorId),
  })
}

export function useUpdateMyProfileMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: { username?: string; bio?: string; avatar?: string }) => updateMyProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userProfile() })
    },
  })
}

export function useUploadUserAvatarMutation() {
  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (progress: number) => void }) =>
      uploadUserAvatar(file, onProgress),
  })
}
