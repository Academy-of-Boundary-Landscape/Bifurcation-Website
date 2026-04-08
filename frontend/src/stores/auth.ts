import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/models'
import type { SsoExchangeResponse, SsoLoginUrlResponse } from '@/types/api'
import { post, get, patch } from '@/services/http'

const TOKEN_KEY = 'auth_access_token'
const USER_KEY = 'auth_user'
const SSO_STATE_KEY = 'auth_sso_state'
const SSO_STATE_META_KEY = 'auth_sso_state_meta'

const isDev = import.meta.env.DEV
function devLog(msg: string, data?: unknown) {
  if (isDev) console.info(msg, data)
}
function devWarn(msg: string, data?: unknown) {
  if (isDev) console.warn(msg, data)
}

type SsoStateMeta = {
  redirectTo: string
  createdAt: string
  origin: string
}

function summarizeState(state: string | null | undefined) {
  if (!state) return 'missing'
  if (state.length <= 24) return state
  return `${state.slice(0, 12)}...${state.slice(-12)}`
}

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
    const response = await get<SsoLoginUrlResponse>(`/auth/sso/login-url${query}`)
    sessionStorage.setItem(SSO_STATE_KEY, response.state)
    const meta: SsoStateMeta = {
      redirectTo: redirectTo || '/books',
      createdAt: new Date().toISOString(),
      origin: window.location.origin,
    }
    sessionStorage.setItem(SSO_STATE_META_KEY, JSON.stringify(meta))
    devLog('[SSO] login-url received', {
      origin: window.location.origin,
      redirectTo: meta.redirectTo,
      state: summarizeState(response.state),
    })
    return response
  }

  async function beginSsoLogin(redirectTo?: string) {
    const response = await getSsoLoginUrl(redirectTo)
    window.location.href = response.authorize_url
  }

  async function exchangeSsoCode(code: string, state: string) {
    const expectedState = sessionStorage.getItem(SSO_STATE_KEY)
    const stateMetaRaw = sessionStorage.getItem(SSO_STATE_META_KEY)
    const stateMeta = stateMetaRaw ? (JSON.parse(stateMetaRaw) as SsoStateMeta) : null

    devLog('[SSO] callback received', {
      currentOrigin: window.location.origin,
      callbackPath: window.location.pathname,
      expectedState: summarizeState(expectedState),
      actualState: summarizeState(state),
      stateMatched: expectedState === state,
      storedMeta: stateMeta,
    })

    if (!expectedState || expectedState !== state) {
      devWarn('[SSO] state mismatch before exchange, fallback to backend validation', {
        currentOrigin: window.location.origin,
        expectedState: summarizeState(expectedState),
        actualState: summarizeState(state),
        storedMeta: stateMeta,
      })
    }

    const response = await post<SsoExchangeResponse>('/auth/sso/exchange', {
      code,
      state,
    })
    devLog('[SSO] exchange succeeded', {
      redirectTo: response.redirect_to,
      isNewUser: response.is_new_user,
      tokenType: response.token_type,
    })
    sessionStorage.removeItem(SSO_STATE_KEY)
    sessionStorage.removeItem(SSO_STATE_META_KEY)
    saveSession(response.access_token)
    const user = await fetchCurrentUser()
    devLog('[SSO] local session user resolved', {
      id: user.id,
      username: user.username,
      role: user.role,
      isAdmin: user.role === 'admin',
    })
    if (user.role !== 'admin') {
      devWarn('[SSO] user is not admin after login', {
        username: user.username,
        role: user.role,
        hint: '检查 Casdoor token 是否包含 roles/role=admin，以及后端 SSO_ADMIN_* 配置是否匹配',
      })
    }
    return response
  }

  // 方法 - 获取当前用户信息
  async function fetchCurrentUser() {
    try {
      const user = await get<User>('/auth/me')
      currentUser.value = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      devLog('[Auth] fetched current user', {
        id: user.id,
        username: user.username,
        role: user.role,
        isActive: user.is_active,
      })
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
    sessionStorage.removeItem(SSO_STATE_META_KEY)
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
    getSsoLoginUrl,
    beginSsoLogin,
    exchangeSsoCode,
    logout,
    fetchCurrentUser,
    updateProfile,
  }
})
