import { get, patch, upload } from '@/services/http'
import type { StoryNode, User } from '@/types/models'

export async function fetchMyProfile() {
  return get<User>('/auth/me')
}

export async function updateMyProfile(payload: { username?: string; bio?: string; avatar?: string }) {
  return patch<User>('/auth/me', payload)
}

export async function uploadUserAvatar(file: File, onProgress?: (progress: number) => void) {
  return upload<{ url: string }>('/uploads/', file, onProgress)
}

export async function fetchUserNodes(params: { authorId: number; limit?: number }) {
  const queryParams = new URLSearchParams()
  if (params.limit !== undefined) queryParams.append('limit', params.limit.toString())

  const suffix = queryParams.toString() ? `?${queryParams.toString()}` : ''
  return get<StoryNode[]>(`/story/user/${params.authorId}/nodes${suffix}`)
}
