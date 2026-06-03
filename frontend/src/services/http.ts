import axios, { AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { notifyRateLimited } from '@/services/notify'

// 创建 axios 实例
const http = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 token
http.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    const token = authStore.accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一错误处理
http.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    // 401 未授权 - 清除登录状态
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
    }
    // 429 限流 - 全局提示（不吞错误，调用方错误态照常触发）
    if (error.response?.status === 429) {
      const detail = (error.response.data as { detail?: string } | undefined)?.detail
      notifyRateLimited(detail)
    }
    return Promise.reject(error)
  }
)

// 通用 GET 请求
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await http.get<T>(url, config)
  return response.data
}

// 列表查询：body 是裸数组，真实总数从 X-Total-Count 响应头读取（缺失则回退到当前页长度）
export interface ListResult<T> {
  items: T[]
  total: number
}

export async function getList<T>(url: string, config?: AxiosRequestConfig): Promise<ListResult<T>> {
  const response = await http.get<T[]>(url, config)
  const items = response.data ?? []
  const header = response.headers['x-total-count']
  const total = header != null && header !== '' ? Number(header) : items.length
  return { items, total: Number.isFinite(total) ? total : items.length }
}

// 通用 POST 请求
export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await http.post<T>(url, data, config)
  return response.data
}

// 通用 PUT 请求
export async function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await http.put<T>(url, data, config)
  return response.data
}

// 通用 PATCH 请求
export async function patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await http.patch<T>(url, data, config)
  return response.data
}

// 通用 DELETE 请求
export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await http.delete<T>(url, config)
  return response.data
}

// 上传文件
export async function upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await http.post<T>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        const progress = Math.round((event.loaded * 100) / event.total)
        onProgress(progress)
      }
    },
  })
  return response.data
}

export default http