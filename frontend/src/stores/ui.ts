import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // 全局 loading 状态
  const globalLoading = ref(false)
  
  // 侧边栏状态 (移动端)
  const sidebarOpen = ref(false)
  
  // 主题模式 (预留扩展)
  const darkMode = ref(true)
  
  // 方法
  function setGlobalLoading(loading: boolean) {
    globalLoading.value = loading
  }
  
  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }
  
  function setSidebarOpen(open: boolean) {
    sidebarOpen.value = open
  }
  
  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }
  
  return {
    globalLoading,
    sidebarOpen,
    darkMode,
    setGlobalLoading,
    toggleSidebar,
    setSidebarOpen,
    toggleDarkMode,
  }
})