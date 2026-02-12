import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const isLoading = ref<boolean>(false)
  const sidebarCollapsed = ref<boolean>(false)
  const theme = ref<'light' | 'dark'>('light')

  // Actions
  const setLoading = (loading: boolean) => {
    isLoading.value = loading
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed
  }

  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
    // 可以在这里保存到 localStorage
    localStorage.setItem('theme', newTheme)
  }

  // 初始化主题
  const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
  if (savedTheme) {
    theme.value = savedTheme
  }

  return {
    isLoading,
    sidebarCollapsed,
    theme,
    setLoading,
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
  }
})