import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/models'
import type { TokenResponse } from '@/types/api'
import { post, get, patch } from '@/services/http'

const TOKEN_KEY = 'auth_access_token'
const USER_KEY = 'auth_user'

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

  // 方法 - 登录
  async function login(emailOrUsername: string, password: string) {
    const formData = new FormData()
    formData.append('username', emailOrUsername)
    formData.append('password', password)
    
    const response = await post<TokenResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    
    accessToken.value = response.access_token
    localStorage.setItem(TOKEN_KEY, response.access_token)
    
    // 获取用户信息
    await fetchCurrentUser()
    
    return response
  }

  // 方法 - 获取当前用户信息
  async function fetchCurrentUser() {
    try {
      const user = await get<User>('/auth/me')
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
  }

  // 方法 - 注册
  async function register(email: string, username: string, password: string) {
    await post('/auth/register', {
      email,
      username,
      password,
    })
  }

  // 方法 - 发送验证码
  async function sendCode(email: string) {
    await post('/auth/send-code-for-activation', { email })
  }

  // 方法 - 验证邮箱
  async function verifyEmail(email: string, code: string) {
    await post('/auth/verify-email-for-activation', { email, code })
  }

  // 方法 - 更新用户资料
  async function updateProfile(data: { username?: string; bio?: string; avatar?: string }) {
    const user = await patch<User>('/auth/me', data)
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
    login,
    logout,
    fetchCurrentUser,
    register,
    sendCode,
    verifyEmail,
    updateProfile,
  }
})