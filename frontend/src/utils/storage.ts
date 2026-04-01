import type { User } from '@/types/models'

// 本地存储工具
export class StorageManager {
  private static readonly PREFIX = 'bifurcation_'
  
  // 通用存储方法
  static set<T>(key: string, value: T): void {
    try {
      const serialized = JSON.stringify(value)
      localStorage.setItem(`${this.PREFIX}${key}`, serialized)
    } catch (error) {
      console.error('存储失败:', error)
    }
  }
  
  static get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(`${this.PREFIX}${key}`)
      if (item === null) return null
      return JSON.parse(item) as T
    } catch (error) {
      console.error('读取存储失败:', error)
      return null
    }
  }
  
  static remove(key: string): void {
    try {
      localStorage.removeItem(`${this.PREFIX}${key}`)
    } catch (error) {
      console.error('删除存储失败:', error)
    }
  }
  
  // 用户相关存储
  static setUser(user: User): void {
    this.set<User>('user', user)
  }
  
  static getUser(): User | null {
    return this.get<User>('user')
  }
  
  static clearUser(): void {
    this.remove('user')
  }
  
  // 认证令牌存储
  static setToken(token: string): void {
    this.set<string>('token', token)
  }
  
  static getToken(): string | null {
    return this.get<string>('token')
  }
  
  static clearToken(): void {
    this.remove('token')
  }
  
  // 草稿存储
  static setDraft(key: string, content: string): void {
    this.set<string>(`draft_${key}`, content)
  }
  
  static getDraft(key: string): string | null {
    return this.get<string>(`draft_${key}`)
  }
  
  static clearDraft(key: string): void {
    this.remove(`draft_${key}`)
  }
  
  // 清除所有存储
  static clearAll(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.PREFIX))
      .forEach(key => localStorage.removeItem(key))
  }
}

// 便捷函数
export function setStorage<T>(key: string, value: T): void {
  StorageManager.set(key, value)
}

export function getStorage<T>(key: string): T | null {
  return StorageManager.get(key)
}

export function removeStorage(key: string): void {
  StorageManager.remove(key)
}