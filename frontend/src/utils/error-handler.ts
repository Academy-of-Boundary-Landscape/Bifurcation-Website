import type { ApiErrorResponse, ValidationErrorResponse, ErrorResponse } from '@/types/api'

function hasValidationDetails(error: ApiErrorResponse): error is ValidationErrorResponse {
  return Array.isArray(error.detail)
}

function resolveErrorMessage(error: unknown, customMessage?: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const responseData = (error as {
      response?: { data?: ApiErrorResponse }
      message?: string
    }).response?.data
    if (responseData && 'detail' in responseData) {
      if (hasValidationDetails(responseData)) {
        const firstError = responseData.detail[0]
        return firstError ? `验证错误: ${firstError.msg}` : '验证错误: 未知错误'
      }
      return (responseData as ErrorResponse).detail
    }
  }

  if (customMessage) {
    return customMessage
  }

  if (error instanceof Error) {
    if (error.message.includes('Network Error') || error.message.includes('timeout')) {
      return '网络连接异常，请检查网络'
    }
    return `发生错误: ${error.message}`
  }

  if (typeof error === 'object' && error !== null) {
    const errorResponse = error as ApiErrorResponse
    if ('detail' in errorResponse) {
      if (hasValidationDetails(errorResponse)) {
        const firstError = errorResponse.detail[0]
        return firstError ? `验证错误: ${firstError.msg}` : '验证错误: 未知错误'
      }
      return (errorResponse as ErrorResponse).detail
    }
  }

  return '操作失败，请重试'
}

function notifyError(messageText: string) {
  console.error(messageText)
  if (typeof window !== 'undefined' && typeof window.alert === 'function') {
    window.alert(messageText)
  }
}

// 全局错误处理工具
export function handleError(error: unknown, customMessage?: string): void {
  notifyError(resolveErrorMessage(error, customMessage))
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
