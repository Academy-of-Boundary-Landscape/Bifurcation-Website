import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/models'
import type { SsoExchangeResponse, SsoLoginUrlResponse } from '@/types/api'
import { post, get, patch } from '@/services/http'

const TOKEN_KEY = 'auth_access_token'
const USER_KEY = 'auth_user'
const SSO_STATE_KEY = 'auth_sso_state'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const accessToken = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const savedUser = localStorage.getItem(USER_KEY)
  const currentUser = ref<User | null>(savedUser ? JSON.parse(savedUser) : null)

  // 计算属性
  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')
  const isWriter = computed(() => currentUser.value?.role === 'writer')
  const isBanned = computed(() => currentUser.value?.role === 'banned')

  function saveSession(token: string) {
    accessToken.value = token
    localStorage.setItem(TOKEN_KEY, token)
  }

  async function getSsoLoginUrl(redirectTo?: string) {
    const query = redirectTo ? `?redirect_to=${encodeURIComponent(redirectTo)}` : ''
    const response = await get<SsoLoginUrlResponse>(`/api/v1/auth/sso/login-url${query}`)
    sessionStorage.setItem(SSO_STATE_KEY, response.state)
    return response
  }

  async function beginSsoLogin(redirectTo?: string) {
    const response = await getSsoLoginUrl(redirectTo)
    window.location.href = response.authorize_url
  }

  async function exchangeSsoCode(code: string, state: string) {
    const expectedState = sessionStorage.getItem(SSO_STATE_KEY)
    if (!expectedState || expectedState !== state) {
      throw new Error('SSO 状态校验失败，请重新登录')
    }

    const response = await post<SsoExchangeResponse>('/api/v1/auth/sso/exchange', {
      code,
      state,
    })
    sessionStorage.removeItem(SSO_STATE_KEY)
    saveSession(response.access_token)
    await fetchCurrentUser()
    return response
  }

  // 方法 - 获取当前用户信息
  async function fetchCurrentUser() {
    try {
      const user = await get<User>('/api/v1/auth/me')
      currentUser.value = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      return user
    } catch (error) {
      // 如果获取失败，清除状态
      logout()
      throw error
    }
  }

  // 方法 - 登出
  function logout() {
    accessToken.value = null
    currentUser.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    sessionStorage.removeItem(SSO_STATE_KEY)
  }

  // 方法 - 更新用户资料
  async function updateProfile(data: { username?: string; bio?: string; avatar?: string }) {
    const user = await patch<User>('/api/v1/auth/me', data)
    currentUser.value = user
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return user
  }

  return {
    // 状态
    accessToken,
    currentUser,
    // 计算属性
    isAuthenticated,
    isAdmin,
    isWriter,
    isBanned,
    // 方法
    getSsoLoginUrl,
    beginSsoLogin,
    exchangeSsoCode,
    logout,
    fetchCurrentUser,
    updateProfile,
  }
})
