s<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar, NDivider } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref } from 'vue'
import type { StoryNodeRead, StoryNode, Comment } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, post } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'

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
const { data: children } = useQuery<StoryNode[]>({
  queryKey: ['node-children', nodeId],
  queryFn: () => {
    // 从树结构中过滤出子节点
    return get<StoryNode[]>(`/story/tree?book_id=${node.value?.book_id || 0}`)
  },
  enabled: !!node.value,
})

// 获取评论
const { data: comments } = useQuery<Comment[]>({
  queryKey: ['node-comments', nodeId],
  queryFn: () => get<Comment[]>(`/interaction/node/${nodeId.value}/comments`),
})

// 点赞
const { mutate: toggleLike } = useMutation({
  mutationFn: () => post<{ action: string; likes_count: number }>(`/interaction/node/${nodeId.value}/like`),
  onSuccess: (data) => {
    message.success(data.action === 'like' ? '点赞成功' : '已取消点赞')
  },
})

// 评论表单
const commentContent = ref('')
const { mutate: submitComment } = useMutation({
  mutationFn: () => post(`/interaction/node/${nodeId.value}/comment`, { content: commentContent.value }),
  onSuccess: () => {
    message.success('评论成功')
    commentContent.value = ''
  },
})

function handleContinue() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'story-write', params: { bookId: node.value?.book_id }, query: { parentId: nodeId.value, mode: 'continue' } })
}

function handleBranch() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  router.push({ name: 'story-write', params: { bookId: node.value?.book_id }, query: { parentId: nodeId.value, mode: 'branch' } })
}
</script>

<template>
  <div>
    <n-spin :show="isLoading">
      <n-space vertical :size="16">
        <!-- 路径导航 -->
        <n-card v-if="path && path.length > 0" class="bg-#1a1a1a border-#2a2a2a">
          <div class="flex items-center flex-wrap gap-2">
            <span class="text-#666666">路径:</span>
            <template v-for="(item, index) in path" :key="item.id">
              <RouterLink 
                :to="`/story/node/${item.id}`" 
                class="text-#8b5cf6 hover:underline"
              >
                {{ item.branch_name || item.title || `节点${item.id}` }}
              </RouterLink>
              <span v-if="index < path.length - 1" class="text-#666666">→</span>
            </template>
          </div>
        </n-card>

        <!-- 节点元信息 -->
        <n-card v-if="node" class="bg-#1a1a1a border-#2a2a2a">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h1 class="text-2xl font-bold text-white mb-2">
                {{ node.title || node.branch_name || '无标题' }}
              </h1>
              <div class="flex items-center gap-4 text-#666666">
                <n-avatar :size="24">
                  {{ node.author?.username?.charAt(0).toUpperCase() }}
                </n-avatar>
                <span>{{ node.author?.username }}</span>
                <span>{{ new Date(node.created_at).toLocaleDateString('zh-CN') }}</span>
              </div>
            </div>
            <n-tag :type="node.status === 'published' ? 'success' : 'warning'">
              {{ node.status }}
            </n-tag>
          </div>
          
          <!-- 操作按钮 -->
          <n-space class="mb-4">
            <n-button type="primary" @click="() => toggleLike()">
              👍 {{ node.likes_count }}
            </n-button>
            <n-button @click="handleContinue">
              ✍️ 沿此续写
            </n-button>
            <n-button @click="handleBranch">
              🌿 创建分支
            </n-button>
          </n-space>
        </n-card>

        <!-- 正文内容 -->
        <n-card v-if="node?.content" class="bg-#1a1a1a border-#2a2a2a">
          <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
            {{ node.content }}
          </div>
        </n-card>

        <!-- 子分支列表 -->
        <n-card v-if="node" class="bg-#1a1a1a border-#2a2a2a">
          <template #header>
            <h2 class="text-xl font-bold text-white">子分支 ({{ node.likes_count }})</h2>
          </template>
          <div class="text-center py-10 text-#666666">
            暂无子分支，成为第一个续写的人！
          </div>
        </n-card>

        <!-- 评论区 -->
        <n-card class="bg-#1a1a1a border-#2a2a2a">
          <template #header>
            <h2 class="text-xl font-bold text-white">评论区</h2>
          </template>
          
          <!-- 发表评论 -->
          <div v-if="authStore.isAuthenticated" class="mb-6">
            <n-input
              v-model:value="commentContent"
              type="textarea"
              placeholder="写下你的评论..."
              :rows="3"
              class="mb-2"
            />
            <n-button type="primary" @click="() => submitComment()" :disabled="!commentContent.trim()">
              发表评论
            </n-button>
          </div>
          <div v-else class="mb-6 text-#666666">
            请登录后发表评论
          </div>
          
          <!-- 评论列表 -->
          <div v-if="comments && comments.length > 0" class="space-y-4">
            <div v-for="comment in comments" :key="comment.id" class="border-b border-#2a2a2a pb-4">
              <div class="flex items-center gap-2 mb-2">
                <n-avatar :size="24">
                  {{ comment.user?.username?.charAt(0).toUpperCase() }}
                </n-avatar>
                <span class="text-white">{{ comment.user?.username }}</span>
                <span class="text-#666666 text-sm">{{ new Date(comment.created_at).toLocaleDateString('zh-CN') }}</span>
              </div>
              <p class="text-#d9d9d9">{{ comment.content }}</p>
            </div>
          </div>
          <div v-else class="text-center py-10 text-#666666">
            暂无评论
          </div>
        </n-card>
      </n-space>
    </n-spin>
  </div>
</template>