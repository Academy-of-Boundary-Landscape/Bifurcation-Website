import { formatDistanceToNow, format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 日期格式化工具
export class DateUtils {
  // 格式化为相对时间（如：2小时前，3天前）
  static formatRelative(date: string | Date): string {
    try {
      const parsedDate = typeof date === 'string' ? parseISO(date) : date
      return formatDistanceToNow(parsedDate, { 
        locale: zhCN,
        addSuffix: true 
      })
    } catch (error) {
      console.error('相对时间格式化失败:', error)
      return '未知时间'
    }
  }
  
  // 格式化为指定格式
  static formatDate(date: string | Date, formatStr: string = 'yyyy-MM-dd HH:mm'): string {
    try {
      const parsedDate = typeof date === 'string' ? parseISO(date) : date
      return format(parsedDate, formatStr, { locale: zhCN })
    } catch (error) {
      console.error('日期格式化失败:', error)
      return '未知日期'
    }
  }
  
  // 获取当前时间戳
  static now(): number {
    return Date.now()
  }
  
  // 解析ISO字符串
  static parseISO(dateString: string): Date {
    return parseISO(dateString)
  }
  
  // 比较两个日期
  static isBefore(date1: string | Date, date2: string | Date): boolean {
    try {
      const d1 = typeof date1 === 'string' ? parseISO(date1) : date1
      const d2 = typeof date2 === 'string' ? parseISO(date2) : date2
      return d1 < d2
    } catch (error) {
      console.error('日期比较失败:', error)
      return false
    }
  }
  
  // 获取今天日期
  static today(): Date {
    return new Date()
  }
}

// 便捷函数
export function formatRelative(date: string | Date): string {
  return DateUtils.formatRelative(date)
}

export function formatDate(date: string | Date, formatStr: string = 'yyyy-MM-dd HH:mm'): string {
  return DateUtils.formatDate(date, formatStr)
}

export function now(): number {
  return DateUtils.now()
}