import { ref, onMounted, onUnmounted } from 'vue'

// 页面标题组合式函数
export function usePageTitle(defaultTitle: string = '分岔视界') {
  const title = ref(defaultTitle)
  
  // 设置页面标题
  const setTitle = (newTitle: string) => {
    title.value = newTitle
    document.title = `${newTitle} | 分岔视界`
  }
  
  // 获取当前标题
  const getCurrentTitle = () => {
    return title.value
  }
  
  // 初始化
  onMounted(() => {
    // 设置默认标题
    setTitle(defaultTitle)
  })
  
  // 清理
  onUnmounted(() => {
    // 页面卸载时恢复默认标题
    document.title = defaultTitle
  })
  
  return {
    title,
    setTitle,
    getCurrentTitle
  }
}