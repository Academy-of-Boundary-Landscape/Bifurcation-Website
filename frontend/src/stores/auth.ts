import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe as getMeApi } from '@/services/auth.service'
import type { UserProfile, LoginFormData } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserProfile | null>(null)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isWriter = computed(() => user.value?.role === 'writer')
  const isBanned = computed(() => user.value?.role === 'banned')

  // Actions
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUser = (userData: UserProfile) => {
    user.value = userData
  }

  const login = async (data: LoginFormData) => {
    const response = await loginApi(data)
    setToken(response.data.access_token)
    // 登录成功后获取用户信息
    await fetchUser()
    return response.data
  }

  const fetchUser = async () => {
    if (!token.value) return
    const response = await getMeApi()
    setUser(response.data)
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  const updateUser = (userData: Partial<UserProfile>) => {
    if (user.value) {
      user.value = { ...user.value, ...userData }
    }
  }

  // 初始化时如果有 token，获取用户信息
  if (token.value) {
    fetchUser().catch(() => {
      // 如果获取用户信息失败，清除 token
      logout()
    })
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isWriter,
    isBanned,
    setToken,
    setUser,
    login,
    fetchUser,
    logout,
    updateUser,
  }
})