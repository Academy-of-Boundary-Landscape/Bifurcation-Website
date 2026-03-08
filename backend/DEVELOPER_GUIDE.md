# 前端集成指南 - API 快速参考

> 本文档是前端开发者的 API 集成指南，与 `worklist.md` 配合使用。`worklist.md` 提供详细的接口定义，本文档侧重于实际使用场景和代码示例。

---

## 📋 目录

1. [快速开始](#快速开始)
2. [认证与授权](#认证与授权)
3. [核心业务场景](#核心业务场景)
4. [错误处理](#错误处理)
5. [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 环境配置

```typescript
// 配置 API 基础地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8057'
const API_V1 = `${API_BASE_URL}/api/v1`

// 健康检查
async function checkHealth(): Promise<boolean> {
  const res = await fetch(`${API_BASE_URL}/health`)
  const data = await res.json()
  return data.status === 'ok'
}
```

### 通用请求封装

```typescript
// services/api.ts
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  requiresAuth?: boolean
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    requiresAuth = false,
  } = options

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  // 添加认证 Token
  if (requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await fetch(`${API_V1}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  // 处理错误响应
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail as string)
  }

  return res.json()
}
```

---

## 🔐 认证与授权

### Token 管理

```typescript
// stores/auth.ts
interface AuthState {
  accessToken: string | null
  user: User | null
}

// 登录
async function login(emailOrUsername: string, password: string) {
  const formData = new URLSearchParams()
  formData.append('username', emailOrUsername)
  formData.append('password', password)
  formData.append('grant_type', 'password')

  const res = await fetch(`${API_V1}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  })

  const data = await res.json()
  if (res.ok) {
    localStorage.setItem('access_token', data.access_token)
    // 获取用户信息
    await fetchUserProfile()
  } else {
    throw new Error(data.detail || '登录失败')
  }
}

// 登出
function logout() {
  localStorage.removeItem('access_token')
  user.value = null
}

// 获取当前用户信息
async function fetchUserProfile() {
  const user = await request<UserProfile>('/auth/me', { requiresAuth: true })
  user.value = user
  return user
}
```

### 注册流程

```typescript
// 完整注册流程
async function register(email: string, username: string, password: string) {
  // 1. 发送邮箱验证码
  await request('/auth/send-code-for-activation', {
    method: 'POST',
    body: { email },
  })

  // 2. 提示用户输入验证码
  const code = await promptForVerificationCode()

  // 3. 验证邮箱验证码
  await request('/auth/verify-email-for-activation', {
    method: 'POST',
    body: { email, code },
  })

  // 4. 完成注册
  const user = await request<User>('/auth/register', {
    method: 'POST',
    body: { email, username, password },
  })

  return user
}
```

---

## 📖 核心业务场景

### 场景 1: 获取活动列表并展示

```typescript
// services/story.service.ts
interface StoryBook {
  id: number
  title: string
  description: string
  cover_image: string | null
  phase: 'drafting' | 'writing' | 'showcase' | 'archived'
  allow_new_nodes: boolean
  start_at: string | null
  writing_end_at: string | null
  showcase_end_at: string | null
  created_at: string
}

async function getBooks(phase?: StoryBook['phase']): Promise<StoryBook[]> {
  const params = new URLSearchParams()
  if (phase) params.append('phase', phase)
  
  return request(`/story/books?${params}`)
}

// 组件中使用
const books = ref<StoryBook[]>([])
books.value = await getBooks('writing')
```

### 场景 2: 获取故事树并渲染

```typescript
interface StoryNodeTree {
  id: number
  parent_id: number | null
  title: string | null
  summary: string | null
  branch_name: string | null
  author: { id: number; username: string; avatar: string | null }
  likes_count: number
  comments_count: number
  children_count: number
  children: StoryNodeTree[]
  created_at: string
}

async function getStoryTree(bookId: number): Promise<StoryNodeTree[]> {
  return request(`/story/tree?book_id=${bookId}`)
}

// 递归渲染树组件
function renderNode(node: StoryNodeTree) {
  return (
    <div class="node">
      <div class="node-header">
        <span class="branch-name">{node.branch_name}</span>
        <span class="author">{node.author.username}</span>
        <span class="stats">
          ❤️ {node.likes_count} 💬 {node.comments_count}
        </span>
      </div>
      {node.children.map(child => renderNode(child))}
    </div>
  )
}
```

### 场景 3: 续写故事

```typescript
interface CreateNodeParams {
  book_id: number
  parent_id?: number
  title?: string
  content: string
  branch_name?: string
  summary?: string
  zone?: 'long' | 'short'
}

async function createNode(params: CreateNodeParams): Promise<StoryNode> {
  const node = await request<StoryNode>('/story/node', {
    method: 'POST',
    requiresAuth: true,
    body: params,
  })

  // 根据返回的状态提示用户
  if (node.status === 'pending') {
    showToast('续写已提交，等待审核')
  } else if (node.status === 'published') {
    showToast('续写发布成功！')
  }

  return node
}
```

### 场景 4: 点赞功能

```typescript
async function toggleLike(nodeId: number): Promise<{ action: 'liked' | 'unliked'; likes_count: number }> {
  const result = await request(`/interaction/node/${nodeId}/like`, {
    method: 'POST',
    requiresAuth: true,
  })
  return result
}

// 组件中使用
const liked = ref(false)
const likesCount = ref(10)

async function handleLike() {
  try {
    const result = await toggleLike(nodeId.value)
    liked.value = result.action === 'liked'
    likesCount.value = result.likes_count
  } catch (e) {
    // 处理未登录情况
    if (e.message.includes('未认证')) {
      router.push('/login')
    }
  }
}
```

### 场景 5: 评论功能

```typescript
interface Comment {
  id: number
  content: string
  created_at: string
  user: { id: number; username: string; avatar: string | null } | null
}

async function getComments(nodeId: number): Promise<Comment[]> {
  return request(`/interaction/node/${nodeId}/comments`)
}

async function addComment(nodeId: number, content: string): Promise<Comment> {
  return request(`/interaction/node/${nodeId}/comment`, {
    method: 'POST',
    requiresAuth: true,
    body: { content },
  })
}

async function deleteComment(commentId: number) {
  await request(`/interaction/comment/${commentId}`, {
    method: 'DELETE',
    requiresAuth: true,
  })
}
```

### 场景 6: 通知系统

```typescript
interface Notification {
  id: number
  type: 'branched' | 'liked' | 'commented' | 'approved' | 'rejected'
  sender: { id: number; username: string; avatar: string | null } | null
  node_id: number | null
  is_read: boolean
  created_at: string
  message: string | null
}

async function getNotifications(): Promise<Notification[]> {
  return request('/interaction/notifications', { requiresAuth: true })
}

async function getUnreadCount(): Promise<number> {
  const res = await request<{ unread_count: number }>('/interaction/notifications/unread-count', {
    requiresAuth: true,
  })
  return res.unread_count
}

async function markAllAsRead() {
  await request('/interaction/notifications/read', {
    method: 'PUT',
    requiresAuth: true,
  })
}

// 轮询未读数量（可选）
setInterval(async () => {
  if (authStore.isAuthenticated) {
    notificationStore.unreadCount = await getUnreadCount()
  }
}, 30000) // 30 秒轮询一次
```

### 场景 7: 管理员审核

```typescript
interface NodeAuditParams {
  status: 'published' | 'archived'
  reject_reason?: string
}

async function getPendingNodes(): Promise<StoryNodeTree[]> {
  return request('/admin/nodes/pending', { requiresAuth: true })
}

async function auditNode(nodeId: number, params: NodeAuditParams): Promise<StoryNodeTree> {
  return request(`/admin/nodes/${nodeId}/audit`, {
    method: 'PATCH',
    requiresAuth: true,
    body: params,
  })
}

// 组件中使用
async function handleApprove(nodeId: number) {
  await auditNode(nodeId, { status: 'published' })
  showToast('已通过审核')
}

async function handleReject(nodeId: number, reason: string) {
  await auditNode(nodeId, { status: 'archived', reject_reason: reason })
  showToast('已驳回')
}
```

---

## ❌ 错误处理

### HTTP 状态码说明

| 状态码 | 说明 | 前端处理建议 |
|--------|------|-------------|
| 200 | 成功 | 正常处理响应数据 |
| 400 | 请求错误 | 显示 `detail` 中的错误信息 |
| 401 | 未认证 | 跳转到登录页 |
| 403 | 无权限 | 显示权限不足提示 |
| 404 | 资源不存在 | 显示 404 页面 |
| 422 | 参数校验失败 | 显示表单验证错误 |
| 500 | 服务器错误 | 显示友好的错误提示 |

### 统一错误处理

```typescript
// utils/error-handler.ts
import { ElMessage } from 'element-plus'

export function handleApiError(error: unknown) {
  const message = error instanceof Error ? error.message : '操作失败'

  if (message.includes('未认证') || message.includes('Unauthorized')) {
    ElMessage.error('请先登录')
    router.push('/login')
  } else if (message.includes('权限')) {
    ElMessage.warning('权限不足')
  } else if (message.includes('不存在')) {
    ElMessage.error('资源不存在')
  } else {
    ElMessage.error(message)
  }
}

// 使用示例
try {
  await createNode(nodeData)
} catch (e) {
  handleApiError(e)
}
```

---

## 🎯 最佳实践

### 1. 请求拦截器

```typescript
// 添加请求拦截器处理 Token 过期
async function requestWithRetry<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  try {
    return await request<T>(endpoint, options)
  } catch (e) {
    // 如果是 401 错误，尝试刷新 Token
    if (e.message.includes('Unauthorized')) {
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        return request<T>(endpoint, options)
      }
    }
    throw e
  }
}
```

### 2. 请求缓存

```typescript
// 简单的请求缓存
const cache = new Map<string, { data: unknown; timestamp: number }>()
const CACHE_TTL = 5 * 60 * 1000 // 5 分钟

async function requestWithCache<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data as T
  }

  const data = await fetcher()
  cache.set(key, { data, timestamp: Date.now() })
  return data
}

// 使用
const books = await requestWithCache('books', () => getBooks())
```

### 3. 防抖处理

```typescript
// 搜索防抖
const search = debounce(async (keyword: string) => {
  if (!keyword.trim()) return []
  return request(`/discovery/search?q=${encodeURIComponent(keyword)}`)
}, 300)
```

### 4. 分页处理

```typescript
interface PaginatedParams {
  skip?: number
  limit?: number
}

async function getBooksWithPagination(page: number, pageSize: number) {
  const skip = (page - 1) * pageSize
  return request(`/story/books?skip=${skip}&limit=${pageSize}`)
}
```

---

## 📊 数据类型定义

```typescript
// types/api.ts

// 用户相关
export interface User {
  id: number
  email: string
  username: string
  role: 'admin' | 'writer' | 'banned'
  is_active: boolean
  is_verified: boolean
  bio: string | null
  avatar: string | null
  nodes_count: number
  likes_count: number
  created_at: string
  updated_at: string
}

// Token
export interface Token {
  access_token: string
  token_type: 'bearer'
}

// 节点状态
export type NodeStatus = 'pending' | 'published' | 'archived'
export type NodeVisibility = 'private' | 'public' | 'unlisted'
export type NodeZone = 'long' | 'short'
export type BookPhase = 'drafting' | 'writing' | 'showcase' | 'archived'

// 通用响应
export interface MessageResponse {
  detail: string
}
```

---

## 🔗 相关文档

- [后端 API 详细文档 (worklist.md)](./worklist.md)
- [Swagger API 文档](http://localhost:8057/docs)
- [ReDoc API 文档](http://localhost:8057/redoc)

---

**文档版本**: 1.0  
**最后更新**: 2026-03-07  
**维护者**: 后端团队