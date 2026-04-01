<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar, NUpload, NIcon, NProgress } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, watch } from 'vue'
import type { UploadOnChange } from 'naive-ui/es/upload/src/public-types'
import type { User, StoryNodeRead } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, put, post } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

// 获取当前用户信息
const { data: user, isLoading, refetch: refetchUser } = useQuery<User>({
  queryKey: ['user-profile'],
  queryFn: () => get<User>('/auth/me'),
})

// 获取用户投稿的节点列表
const { data: submittedNodes, isLoading: nodesLoading, refetch: refetchNodes } = useQuery<StoryNodeRead[]>({
  queryKey: ['user-nodes'],
  queryFn: () => get<StoryNodeRead[]>(`/story/node?author_id=${authStore.currentUser?.id}&limit=5`),
  enabled: !!authStore.currentUser?.id,
})

// 更新用户资料
const { mutate: updateUser, isPending: updatingUser } = useMutation({
  mutationFn: (userData: Partial<User>) => put<User>(`/auth/me`, userData),
  onSuccess: (updatedUser) => {
    message.success('资料更新成功')
    // 更新全局状态
    authStore.currentUser = updatedUser
  },
  onError: (error) => {
    console.error('更新失败:', error)
    message.error('更新失败，请重试')
  }
})

// 上传头像
const { mutate: uploadAvatar, isPending: uploadingAvatar } = useMutation({
  mutationFn: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return post<{ url: string }>('/uploads/', formData)
  },
  onSuccess: (data) => {
    message.success('头像上传成功')
    // 更新用户资料中的头像
    if (user.value) {
      const updatedUser = { ...user.value, avatar: data.url }
      updateUser(updatedUser)
    }
  },
  onError: (error) => {
    console.error('上传失败:', error)
    message.error('头像上传失败，请重试')
  }
})

// 用户资料表单
const form = ref({
  username: '',
  bio: '',
  avatar: '',
})

// 头像文件选择
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(null)

// 初始化表单数据
onMounted(() => {
  if (user.value) {
    form.value.username = user.value.username || ''
    form.value.bio = user.value.bio || ''
    form.value.avatar = user.value.avatar || ''
    avatarPreview.value = user.value.avatar || null
  }
})

// 文件选择处理
const handleFileChange: UploadOnChange = ({ file }) => {
  if (file.file) {
    avatarFile.value = file.file
    
    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        avatarPreview.value = e.target.result as string
      }
    }
    reader.readAsDataURL(file.file)
  }
}

// 提交用户资料更新
function handleSubmit() {
  if (!form.value.username.trim()) {
    message.error('用户名不能为空')
    return
  }
  
  // 如果有新头像，先上传
  if (avatarFile.value) {
    uploadAvatar(avatarFile.value)
  } else {
    // 没有新头像，直接更新其他资料
    updateUser(form.value)
  }
}

// 上传进度
const uploadProgress = ref<number>(0)

// 监听上传状态
watch(uploadingAvatar, (newVal) => {
  if (newVal) {
    uploadProgress.value = 0
    // 模拟上传进度
    const interval = setInterval(() => {
      if (uploadProgress.value < 100) {
        uploadProgress.value += 10
      }
      if (uploadProgress.value >= 100) {
        clearInterval(interval)
      }
    }, 100)
  }
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <n-spin :show="isLoading">
      <!-- 用户基本信息 -->
      <n-card class="bg-#1a1a1a border-#2a2a2a mb-6">
        <template #header>
          <h1 class="text-3xl font-bold text-white">个人中心</h1>
          <p class="text-#666666 mt-2">管理您的账户和创作</p>
        </template>
        
        <div class="flex flex-col md:flex-row gap-8">
          <!-- 头像区域 -->
          <div class="flex-shrink-0">
            <div class="flex flex-col items-center gap-4">
              <div class="relative">
                <n-avatar 
                  :size="120" 
                  :src="avatarPreview || user?.avatar || undefined"
                >
                  {{ user?.username?.charAt(0).toUpperCase() ?? '' }}
                </n-avatar>
                <div class="absolute -bottom-2 -right-2 bg-#8b5cf6 text-white rounded-full w-8 h-8 flex items-center justify-center text-xs">
                  ✏️
                </div>
              </div>
              
              <!-- 上传组件 -->
              <n-upload
                ref="avatarUploadRef"
                :show-file-list="false"
                :multiple="false"
                :custom-request="() => {}"
                @change="handleFileChange"
                accept="image/*"
                :max="1"
              >
                <n-button 
                  size="small" 
                  type="primary" 
                  secondary
                >
                  更换头像
                </n-button>
              </n-upload>
              
              <!-- 上传进度 -->
              <div v-if="uploadingAvatar" class="w-full">
                <n-progress 
                  :percentage="uploadProgress" 
                  :show-text="true" 
                  :height="8" 
                  color="#8b5cf6"
                />
              </div>
            </div>
          </div>
          
          <!-- 基本信息区域 -->
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold text-white mb-4">{{ user?.username ?? '未登录' }}</h2>
            
            <div class="space-y-4">
              <!-- 用户名 -->
              <div class="flex items-center gap-3">
                <span class="text-#666666 w-24">用户名:</span>
                <input 
                  v-model="form.username" 
                  class="bg-#2a2a2a border border-#2a2a2a rounded-lg px-4 py-2 text-white placeholder-#666666 focus:border-#8b5cf6 focus:outline-none w-full"
                  placeholder="请输入用户名"
                />
              </div>
              
              <!-- 个人简介 -->
              <div class="flex items-center gap-3">
                <span class="text-#666666 w-24">个人简介:</span>
                <textarea 
                  v-model="form.bio" 
                  class="bg-#2a2a2a border border-#2a2a2a rounded-lg px-4 py-2 text-white placeholder-#666666 focus:border-#8b5cf6 focus:outline-none w-full h-24"
                  placeholder="请简单介绍自己..."
                ></textarea>
              </div>
              
              <!-- 个人信息 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="flex items-center gap-3">
                  <span class="text-#666666 w-24">邮箱:</span>
                  <span class="text-#d9d9d9">{{ user?.email }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="text-#666666 w-24">注册时间:</span>
                  <span class="text-#d9d9d9">{{ user?.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '-' }}</span>
                </div>
              </div>
              
              <!-- 角色标签 -->
              <div class="flex items-center gap-3">
                <span class="text-#666666 w-24">角色:</span>
                <n-tag 
                  v-if="user?.role === 'admin'" 
                  type="error"
                  size="small"
                >
                  管理员
                </n-tag>
                <n-tag 
                  v-else-if="user?.role === 'writer'" 
                  type="success"
                  size="small"
                >
                  作者
                </n-tag>
                <n-tag 
                  v-else 
                  type="default"
                  size="small"
                >
                  {{ user?.role }}
                </n-tag>
              </div>
            </div>
            
            <!-- 保存按钮 -->
            <div class="mt-6">
              <n-button 
                type="primary" 
                :loading="updatingUser || uploadingAvatar" 
                @click="handleSubmit"
              >
                保存资料
              </n-button>
            </div>
          </div>
        </div>
      </n-card>
      
      <!-- 用户投稿节点 -->
      <n-card class="bg-#1a1a1a border-#2a2a2a">
        <template #header>
          <h2 class="text-xl font-bold text-white">我的投稿</h2>
          <p class="text-#666666 mt-2">您已投稿 {{ submittedNodes?.length || 0 }} 个节点</p>
        </template>
        
        <n-spin :show="nodesLoading">
          <div v-if="!submittedNodes || submittedNodes.length === 0" class="text-center py-12">
            <p class="text-#666666">暂无投稿节点</p>
              <n-button 
                type="primary" 
                class="mt-4" 
                :component="RouterLink" 
                :to="{ name: 'books' }"
              >
              开始创作
            </n-button>
          </div>
          
          <div v-else class="space-y-4">
            <div 
              v-for="node in submittedNodes" 
              :key="node.id" 
              class="border-b border-#2a2a2a pb-4 last:border-b-0 last:pb-0 hover:bg-#2a2a2a transition-colors cursor-pointer"
              @click="$router.push({ name: 'story-node', params: { nodeId: node.id } })"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <h3 class="text-lg font-semibold text-white mb-1">
                    {{ node.title || node.branch_name || '无标题' }}
                  </h3>
                  <p class="text-#666666 text-sm line-clamp-2">
                    {{ node.content?.substring(0, 100) }}{{ node.content?.length > 100 ? '...' : '' }}
                  </p>
                  <div class="flex items-center gap-3 text-#666666 text-xs mt-2">
                    <span>{{ node.created_at ? new Date(node.created_at).toLocaleDateString('zh-CN') : '-' }}</span>
                    <span>{{ node.status }}</span>
                    <span>{{ node.likes_count || 0 }} 赞</span>
                    <span>{{ node.comments_count || 0 }} 评论</span>
                    <span>{{ node.children_count || 0 }} 分支</span>
                  </div>
                </div>
                <n-avatar 
                  :size="32" 
                  :src="node.author?.avatar ?? undefined"
                  class="flex-shrink-0"
                >
                  {{ node.author?.username?.charAt(0).toUpperCase() }}
                </n-avatar>
              </div>
            </div>
          </div>
        </n-spin>
      </n-card>
    </n-spin>
  </div>
</template>
