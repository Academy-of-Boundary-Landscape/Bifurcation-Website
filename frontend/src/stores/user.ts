import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserProfile } from '@/types'

export const useUserStore = defineStore('user', () => {
  // State
  const userProfile = ref<UserProfile | null>(null)
  const notificationsCount = ref<number>(0)

  // Getters
  const hasProfile = computed(() => !!userProfile.value)

  // Actions
  const setProfile = (profile: UserProfile) => {
    userProfile.value = profile
  }

  const clearProfile = () => {
    userProfile.value = null
  }

  const incrementNotifications = () => {
    notificationsCount.value++
  }

  const clearNotifications = () => {
    notificationsCount.value = 0
  }

  return {
    userProfile,
    notificationsCount,
    hasProfile,
    setProfile,
    clearProfile,
    incrementNotifications,
    clearNotifications,
  }
})