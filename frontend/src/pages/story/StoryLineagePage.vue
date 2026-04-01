<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar, NDivider } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref } from 'vue'
import type { StoryNodeRead, StoryNode } from '@/types/models'
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

// 获取完整分支阅读路径
const { data: lineage } = useQuery<StoryNodeRead[]>({
  queryKey: ['story-lineage', nodeId],
  queryFn: () => get<StoryNodeRead[]>(`/story/node/${nodeId.value}/lineage`),
})

// 点赞
const { mutate: toggleLike, isPending: togglingLike } = useMutation({
  mutationFn: () => post<{ action: string; likes_count: number }>(`/interaction/node/${nodeId.value}/like`),
  onSuccess: (data) => {
    message.success(data.action === 'like' ? '点赞成功' : '已取消点赞')
  },
})

function handleToggleLike() {
  toggleLike()
}

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
  <div class="max-w-4xl mx-auto px-4 py-8">
    <n-spin :show="isLoading">
      <!-- 路径导航 -->
      <n-card v-if="lineage && lineage.length > 0" class="bg-#1a1a1a border-#2a2a2a mb-6">
        <div class="flex items-center flex-wrap gap-2">
          <span class="text-#666666">当前分支:</span>
          <template v-for="(item, index) in lineage" :key="item.id">
            <router-link 
              :to="{ name: 'story-node', params: { nodeId: item.id } }" 
              class="text-#8b5cf6 hover:underline"
              :class="index === lineage.length - 1 ? 'font-bold text-white' : ''"
            >
              {{ item.branch_name || item.title || `节点${item.id}` }}
            </router-link>
            <span v-if="index < lineage.length - 1" class="text-#666666">→</span>
          </template>
        </div>
      </n-card>

      <!-- 完整分支阅读区 -->
      <div v-if="lineage" class="space-y-8">
        <template v-for="(item, index) in lineage" :key="item.id">
          <n-card 
            class="bg-#1a1a1a border-#2a2a2a transition-all duration-300"
            :class="index === lineage.length - 1 ? 'ring-2 ring-#8b5cf6 scale-[1.02]' : 'hover:shadow-lg hover:border-#3a3a3a'"
          >
            <div class="flex justify-between items-start mb-4">
              <div>
                <h2 class="text-xl font-bold text-white mb-2">
                  {{ item.title || item.branch_name || '无标题' }}
                </h2>
                <div class="flex items-center gap-4 text-#666666">
                  <n-avatar 
                    :size="32" 
                    :src="item.author?.avatar ?? undefined"
                  >
                    {{ item.author?.username?.charAt(0).toUpperCase() }}
                  </n-avatar>
                  <span>{{ item.author?.username }}</span>
                  <span>{{ new Date(item.created_at).toLocaleDateString('zh-CN') }}</span>
                  <n-tag :type="item.status === 'published' ? 'success' : 'warning'">
                    {{ item.status }}
                  </n-tag>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-sm text-#666666">第 {{ index + 1 }} 节</span>
                <span class="text-sm text-#666666">·</span>
                <span class="text-sm text-#666666">{{ item.likes_count || 0 }} 赞</span>
              </div>
            </div>
            
            <!-- 正文内容 -->
            <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
              {{ item.content }}
            </div>
            
            <!-- 操作按钮 -->
            <div class="mt-4 pt-4 border-t border-#2a2a2a">
              <nspace>
                <n-button size="small" type="primary" @click="handleToggleLike" :loading="togglingLike && item.id === nodeId">
                  👍 {{ item.likes_count || 0 }} 赞
                </n-button>
                <n-button size="small" @click="$router.push({ name: 'story-node', params: { nodeId: item.id } })">
                  查看详情
                </n-button>
                <n-button v-if="index === lineage.length - 1" size="small" @click="handleContinue">
                  ✍️ 沿此续写
                </n-button>
                <n-button v-if="index === lineage.length - 1" size="small" @click="handleBranch">
                  🌿 创建分支
                </n-button>
              </nspace>
            </div>
          </n-card>
        </template>
      </div>

      <!-- 空状态 -->
      <div v-if="!lineage || lineage.length === 0" class="text-center py-16">
        <div class="text-6xl mb-4">📖</div>
        <h2 class="text-2xl font-bold text-white mb-2">暂无完整分支</h2>
        <p class="text-#666666">该节点尚未形成完整的分支路径，无法查看完整阅读体验</p>
        
        <div class="mt-8">
          <n-button 
            type="primary" 
            size="large" 
            @click="$router.push({ name: 'books' })"
          >
            查看故事册
          </n-button>
        </div>
      </div>
    </n-spin>
  </div>
</template>
