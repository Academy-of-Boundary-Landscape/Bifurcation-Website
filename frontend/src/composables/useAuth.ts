import { useAuthStore } from '@/stores/auth'
import { ref, onMounted } from 'vue'

// 认证组合式函数
export function useAuth() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 登录
  const login = async (emailOrUsername: string, password: string) => {
    loading.value = true
    error.value = null
    try {
      await authStore.login(emailOrUsername, password)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  // 登出
  const logout = () => {
    authStore.logout()
  }
  
  // 注册
  const register = async (email: string, username: string, password: string) => {
    loading.value = true
    error.value = null
    try {
      await authStore.register(email, username, password)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  // 获取当前用户
  const fetchCurrentUser = async () => {
    loading.value = true
    error.value = null
    try {
      await authStore.fetchCurrentUser()
      return authStore.currentUser
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取用户信息失败'
      return null
    } finally {
      loading.value = false
    }
  }
  
  // 检查认证状态
  const isAuthenticated = () => {
    return authStore.isAuthenticated
  }
  
  // 初始化检查
  onMounted(() => {
    if (authStore.accessToken && !authStore.currentUser) {
      fetchCurrentUser()
    }
  })
  
  return {
    login,
    logout,
    register,
    fetchCurrentUser,
    isAuthenticated,
    loading,
    error
  }
}
