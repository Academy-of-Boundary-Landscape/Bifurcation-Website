import { useMessage } from 'naive-ui'
import type { ApiErrorResponse, ValidationErrorResponse, ErrorResponse } from '@/types/api'

// 全局错误处理工具
export function handleError(error: unknown, customMessage?: string): void {
  const message = useMessage()
  
  if (error instanceof Error) {
    // 处理网络错误、请求错误等
    if (error.message.includes('Network Error') || error.message.includes('timeout')) {
      message.error(customMessage || '网络连接异常，请检查网络')
      return
    }
    
    // 处理其他JavaScript错误
    message.error(customMessage || `发生错误: ${error.message}`)
    return
  }
  
  // 处理API错误响应
  if (typeof error === 'object' && error !== null) {
    const errorResponse = error as ApiErrorResponse
    
    if ('detail' in errorResponse) {
      if (Array.isArray((errorResponse as any).detail)) {
        // ValidationErrorResponse
        const validationError = errorResponse as ValidationErrorResponse
        const firstError = validationError.detail[0]
        if (firstError) {
          message.error(customMessage || `验证错误: ${firstError.msg}`)
        } else {
          message.error(customMessage || '验证错误: 未知错误')
        }
      } else {
        // ErrorResponse
        message.error(customMessage || (errorResponse as ErrorResponse).detail)
      }
      return
    }
  }
  
  // 默认错误处理
  message.error(customMessage || '操作失败，请重试')
}

// 创建错误处理器实例
export class ErrorHandler {
  static handle(error: unknown, customMessage?: string): void {
    handleError(error, customMessage)
  }
  
  static createHandler(customMessage?: string) {
    return (error: unknown) => handleError(error, customMessage)
  }
}
