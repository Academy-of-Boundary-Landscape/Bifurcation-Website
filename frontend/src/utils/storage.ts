// 本地存储工具
const PREFIX = 'bifurcation_'

export function setStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(`${PREFIX}${key}`, JSON.stringify(value))
  } catch (error) {
    console.error('存储失败:', error)
  }
}

export function getStorage<T>(key: string): T | null {
  try {
    const item = localStorage.getItem(`${PREFIX}${key}`)
    if (item === null) return null
    return JSON.parse(item) as T
  } catch (error) {
    console.error('读取存储失败:', error)
    return null
  }
}

export function removeStorage(key: string): void {
  try {
    localStorage.removeItem(`${PREFIX}${key}`)
  } catch (error) {
    console.error('删除存储失败:', error)
  }
}
