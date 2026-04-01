<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar, NDivider, NUpload, NIcon, NProgress } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, watch } from 'vue'
import type { StoryNodeRead, StoryNode } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, post, put, delete } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import { UploadFileInfo } from 'naive-ui/es/upload/src/interface'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const nodeId = computed(() => Number(route.params.nodeId))

// 获取节点详情
const { data: node, isLoading } = useQuery<StoryNodeRead>({
  queryKey: ['story-node', nodeId],
  queryFn: () => get<StoryNodeRead>(`/story/node/${nodeId.value}`),
})

// 获取阅读路径
const { data: path } = useQuery<StoryNode[]>({
  queryKey: ['node-path', nodeId],
  queryFn: () => get<StoryNode[]>(`/story/node/${nodeId.value}/path`),
})

// 获取子分支
const { data: children } = useQuery<StoryNodeRead[]>({
  queryKey: ['node-children', nodeId],
  queryFn: () => get<StoryNodeRead[]>(`/story/node?parent_id=${nodeId.value}&limit=5`),
  enabled: !!node.value,
})

// 获取评论
const { data: comments } = useQuery({
  queryKey: ['node-comments', nodeId],
  queryFn: () => get(`/interaction/node/${nodeId.value}/comments`),
})

// 点赞
const { mutate: toggleLike, isPending: togglingLike } = useMutation({
  mutationFn: () => post<{ action: string; likes_count: number }>(`/interaction/node/${nodeId.value}/like`),
  onSuccess: (data) => {
    message.success(data.action === 'like' ? '点赞成功' : '已取消点赞')
  },
})

// 提交评论
const commentContent = ref('')
const { mutate: submitComment, isPending: submittingComment } = useMutation({
  mutationFn: () => post(`/interaction/node/${nodeId.value}/comment`, { content: commentContent.value }),
  onSuccess: () => {
    message.success('评论成功')
    commentContent.value = ''
  },
})

// 删除评论
const { mutate: deleteComment, isPending: deletingComment } = useMutation({
  mutationFn: (commentId: number) => delete(`/interaction/node/${nodeId.value}/comment/${commentId}`),
  onSuccess: (_, commentId) => {
    message.success('评论已删除')
    // 更新评论列表
    if (comments.value) {
      const updatedComments = comments.value.filter((c: any) => c.id !== commentId)
      comments.value = updatedComments
    }
  },
})

// 处理续写
function handleContinue() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'story-write', params: { bookId: node.value?.book_id }, query: { parentId: nodeId.value, mode: 'continue' } })
}

// 处理创建分支
function handleBranch() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'story-write', params: { bookId: node.value?.book_id }, query: { parentId: nodeId.value, mode: 'branch' } })
}

// 处理编辑节点
function handleEdit() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'story-write', params: { bookId: node.value?.book_id }, query: { nodeId: nodeId.value, mode: 'edit' } })
}

// 处理删除节点
function handleDelete() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  
  // 确认对话框
  message.info(
    '确定要删除这个节点吗？',
    {
      title: '确认删除',
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await delete(`/story/node/${nodeId.value}`)
          message.success('节点删除成功')
          // 返回书籍详情页
          router.push({ name: 'books' })
        } catch (error) {
          console.error('删除失败:', error)
          message.error('删除失败，请重试')
        }
      }
    }
  )
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <n-spin :show="isLoading">
      <!-- 路径导航 -->
      <story-branch-path v-if="path && path.length > 0" :path="path" />

      <!-- 节点元信息 -->
      <n-card v-if="node" class="bg-#1a1a1a border-#2a2a2a mb-6">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h1 class="text-2xl font-bold text-white mb-2">
              {{ node.title ?? node.branch_name ?? '无标题' }}
            </h1>
            <div class="flex items-center gap-4 text-#666666">
              <n-avatar 
                :size="32" 
                :src="node.author?.avatar ?? ''"
              >
                {{ node.author?.username?.charAt(0).toUpperCase() ?? '' }}
              </n-avatar>
              <span>{{ node.author?.username ?? '系统' }}</span>
              <span>{{ new Date(node.created_at).toLocaleDateString('zh-CN') }}</span>
            </div>
          </div>
          <n-tag :type="node.status === 'published' ? 'success' : 'warning'">
            {{ node.status }}
          </n-tag>
        </div>
        
        <!-- 操作按钮 -->
        <nspace class="mb-4">
          <n-button type="primary" @click="() => toggleLike()" :loading="togglingLike && node?.id === nodeId.value">
            👍 {{ node.likes_count ?? 0 }} 赞
          </n-button>
          <n-button @click="handleContinue">
            ✍️ 沿此续写
          </n-button>
          <n-button @click="handleBranch">
            🌿 创建分支
          </n-button>
          
          <!-- 编辑和删除按钮（仅作者可见） -->
          <n-button 
            v-if="authStore.currentUser?.id === node.author?.id" 
            type="default" 
            @click="handleEdit"
          >
            ✏️ 编辑
          </n-button>
          <n-button 
            v-if="authStore.currentUser?.id === node.author?.id" 
            type="error" 
            @click="handleDelete"
          >
            ❌ 删除
          </n-button>
        </nspace>
      </n-card>

      <!-- 正文内容 -->
      <n-card v-if="node?.content" class="bg-#1a1a1a border-#2a2a2a mb-6">
        <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
          {{ node.content }}
        </div>
      </n-card>

      <!-- 子分支列表 -->
      <n-card v-if="children && children.length > 0" class="bg-#1a1a1a border-#2a2a2a">
        <template #header>
          <h2 class="text-xl font-bold text-white">子分支（{{ children.length }}）</h2>
        </template>
        
        <div class="space-y-4">
          <div 
            v-for="child in children" 
            :key="child.id" 
            class="border-b border-#2a2a2a pb-4 last:border-b-0 last:pb-0 hover:bg-#2a2a2a transition-colors cursor-pointer"
            @click="$router.push({ name: 'story-node', params: { nodeId: child.id } })"
          >
            <div class="flex items-center gap-3">
              <n-avatar 
                :size="32" 
                :src="child.author?.avatar"
              >
                {{ child.author?.username?.charAt(0).toUpperCase() }}
              </n-avatar>
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-semibold text-white">{{ child.title || child.branch_name || '无标题' }}</h3>
                <p class="text-#666666 text-sm line-clamp-2">
                  {{ child.content?.substring(0, 100) }}{{ child.content?.length > 100 ? '...' : '' }}
                </p>
                <div class="flex items-center gap-2 text-#666666 text-xs mt-2">
                  <span>{{ new Date(child.created_at).toLocaleDateString('zh-CN') }}</span>
                  <span>{{ child.status }}</span>
                  <span>{{ child.likes_count }} 赞</span>
                  <span>{{ child.comments_count }} 评论</span>
                  <span>{{ child.children_count }} 分支</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-card>
      
      <!-- 子分支空状态 -->
      <n-card v-if="node && (!children || children.length === 0)" class="bg-#1a1a1a border-#2a2a2a">
        <template #header>
          <h2 class="text-xl font-bold text-white">子分支（{{ children?.length || 0 }}）</h2>
        </template>
        
        <div class="text-center py-12">
          <p class="text-#666666">暂无子分支，成为第一个创建者！</p>
          
          <div class="mt-4">
            <n-button 
              type="primary" 
              size="large" 
              @click="handleBranch"
            >
              开始创建新分支
            </n-button>
          </div>
        </div>
      </n-card>
      
      <!-- 评论区 -->
      <n-card class="bg-#1a1a1a border-#2a2a2a">
        <template #header>
          <h2 class="text-xl font-bold text-white">评论区（{{ comments?.length || 0 }}）</h2>
        </template>
        
        <!-- 发表评论 -->
        <div v-if="authStore.isAuthenticated" class="mb-6">
          <textarea 
            v-model="commentContent" 
            class="w-full bg-#2a2a2a border border-#2a2a2a rounded-lg px-4 py-2 text-white placeholder-#666666 focus:border-#8b5cf6 focus:outline-none h-24"
            placeholder="写下您的评论..."
          ></textarea>
          <div class="mt-4">
            <n-button 
              type="primary" 
              @click="submitComment"
              :loading="submittingComment"
              :disabled="!commentContent.trim() || submittingComment"
            >
              发表评论
            </n-button>
          </div>
        </div>
        
        <!-- 登录提示 -->
        <div v-else class="mb-6 text-#666666">
          请登录后发表评论
        </div>
        
        <!-- 评论列表 -->
        <div v-if="comments && comments.length > 0" class="space-y-4">
          <div 
            v-for="comment in comments" 
            :key="comment.id" 
            class="border-b border-#2a2a2a pb-4 last:border-b-0 last:pb-0 flex items-start gap-3"
          >
            <n-avatar 
              :size="24" 
              :src="comment.user?.avatar"
              class="mt-1"
            >
              {{ comment.user?.username?.charAt(0).toUpperCase() }}
            </n-avatar>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-white">{{ comment.user?.username }}</span>
                <span class="text-#666666 text-sm">{{ new Date(comment.created_at).toLocaleDateString('zh-CN') }}</span>
                <!-- 删除按钮（仅评论作者可见） -->
                <n-button 
                  v-if="authStore.currentUser?.id === comment.user?.id" 
                  size="small" 
                  type="error" 
                  @click="() => deleteComment(comment.id)"
                  :loading="deletingComment && comments.find(c => c.id === comment.id)?.id === comment.id"
                  :disabled="deletingComment && comments.find(c => c.id === comment.id)?.id === comment.id"
                >
                  删除
                </n-button>
              </div>
              
              <p class="text-#d9d9d9 mt-2">{{ comment.content }}</p>
            </div>
          </div>
        </div>
        
        <!-- 评论空状态 -->
        <div v-else class="text-center py-12">
          <p class="text-#666666">暂无评论</p>
          
          <div class="mt-4">
            <n-button 
              v-if="authStore.isAuthenticated" 
              type="primary" 
              size="large" 
              @click="() => $refs.commentTextarea.focus()"
            >
              成为第一个评论者
            </n-button>
          </div>
        </div>
      </n-card>
    </n-spin>
  </div>
</template>
</content>
<task_progress>
- [x] 分析 ProfilePage.vue 当前实现
- [x] 实现 ProfilePage.vue 头像上传功能
- [x] 实现 NotificationPage.vue 筛选功能
- [x] 完善 StoryNodePage.vue 功能
- [ ] 完善 StoryTreeFlow.vue 功能
</task_progress>
