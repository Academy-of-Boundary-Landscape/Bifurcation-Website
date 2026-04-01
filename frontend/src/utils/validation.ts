import type { UserCreate, StoryNodeCreate } from '@/types/models'

// 表单验证工具
export class ValidationUtils {
  // 邮箱验证
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }
  
  // 密码强度验证
  static isValidPassword(password: string): { valid: boolean; message: string } {
    if (password.length < 8) {
      return { valid: false, message: '密码长度至少8位' }
    }
    
    if (!/[A-Z]/.test(password)) {
      return { valid: false, message: '密码必须包含至少一个大写字母' }
    }
    
    if (!/[a-z]/.test(password)) {
      return { valid: false, message: '密码必须包含至少一个小写字母' }
    }
    
    if (!/[0-9]/.test(password)) {
      return { valid: false, message: '密码必须包含至少一个数字' }
    }
    
    return { valid: true, message: '密码符合要求' }
  }
  
  // 用户名验证
  static isValidUsername(username: string): { valid: boolean; message: string } {
    if (username.length < 3) {
      return { valid: false, message: '用户名长度至少3位' }
    }
    
    if (username.length > 20) {
      return { valid: false, message: '用户名长度不能超过20位' }
    }
    
    if (!/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(username)) {
      return { valid: false, message: '用户名只能包含字母、数字、下划线和中文' }
    }
    
    return { valid: true, message: '用户名符合要求' }
  }
  
  // 故事节点内容验证
  static validateStoryNode(node: Partial<StoryNodeCreate>): { valid: boolean; errors: string[] } {
    const errors: string[] = []
    
    if (!node.content || node.content.trim().length < 50) {
      errors.push('内容长度至少50字')
    }
    
    if (node.content && node.content.trim().length > 2000) {
      errors.push('内容长度不能超过2000字')
    }
    
    if (node.branch_name && node.branch_name.trim().length < 2) {
      errors.push('分支名称至少2个字符')
    }
    
    if (node.branch_name && node.branch_name.trim().length > 50) {
      errors.push('分支名称不能超过50个字符')
    }
    
    return {
      valid: errors.length === 0,
      errors
    }
  }
  
  // 用户注册验证
  static validateUserRegistration(user: UserCreate): { valid: boolean; errors: string[] } {
    const errors: string[] = []
    
    if (!user.email || !this.isValidEmail(user.email)) {
      errors.push('请输入有效的邮箱地址')
    }
    
    if (!user.username || !this.isValidUsername(user.username).valid) {
      errors.push(this.isValidUsername(user.username).message)
    }
    
    if (!user.password || !this.isValidPassword(user.password).valid) {
      errors.push(this.isValidPassword(user.password).message)
    }
    
    return {
      valid: errors.length === 0,
      errors
    }
  }
}

// 便捷函数
export function isValidEmail(email: string): boolean {
  return ValidationUtils.isValidEmail(email)
}

export function isValidPassword(password: string): { valid: boolean; message: string } {
  return ValidationUtils.isValidPassword(password)
}

export function isValidUsername(username: string): { valid: boolean; message: string } {
  return ValidationUtils.isValidUsername(username)
}

export function validateStoryNode(node: Partial<StoryNodeCreate>): { valid: boolean; errors: string[] } {
  return ValidationUtils.validateStoryNode(node)
}

export function validateUserRegistration(user: UserCreate): { valid: boolean; errors: string[] } {
  return ValidationUtils.validateUserRegistration(user)
}