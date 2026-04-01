<script setup lang="ts">
import { NCard, NAvatar, NButton } from 'naive-ui'
import { ref, computed, onMounted } from 'vue'
import type { Comment } from '@/types/models'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { get, post } from '@/services/http'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  nodeId: number
}>()

const emits = defineEmits(['comment-added'])

const authStore = useAuthStore()
const queryClient = useQueryClient()
const comments = ref<Comment[]>([])

// 获取评论列表
const { data: commentData, isLoading, refetch } = useQuery<Comment[]>({
  queryKey: ['node-comments', props.nodeId],
  queryFn: () => get<Comment[]>(`/interaction/node/${props.nodeId}/comments`),
})

// 删除评论
const { mutate: deleteComment } = useMutation({
  mutationFn: (commentId: number) => post(`/interaction/comment/${commentId}/delete`),
  onSuccess: () => {
    // 刷新评论列表
    refetch()
  }
})

// 初始化
onMounted(() => {
  if (commentData.value) {
    comments.value = commentData.value
  }
})
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-bold text-white">评论区 ({{ comments.length }})</h3>
        <n-button size="small" @click="() => refetch()" v-if="!isLoading">刷新</n-button>
      </div>
    </template>
    
    <div v-if="isLoading" class="text-center py-8">
      <p class="text-#666666">加载中...</p>
    </div>
    
    <div v-else-if="comments.length === 0" class="text-center py-8">
      <p class="text-#666666">暂无评论，快来发表第一条评论吧！</p>
    </div>
    
    <div v-else class="space-y-4">
      <div v-for="comment in comments" :key="comment.id" class="border-b border-#2a2a2a pb-4 last:border-b-0 last:pb-0">
        <div class="flex items-start gap-3">
          <n-avatar :size="32">
            {{ comment.user?.username?.charAt(0).toUpperCase() }}
          </n-avatar>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium text-white">{{ comment.user?.username }}</span>
              <span class="text-#666666 text-sm">{{ new Date(comment.created_at).toLocaleString('zh-CN') }}</span>
            </div>
            <p class="text-#d9d9d9">{{ comment.content }}</p>
          </div>
          <div v-if="authStore.isAuthenticated && comment.user?.id === authStore.currentUser?.id" class="flex flex-col items-end">
            <n-button size="small" @click="() => deleteComment(comment.id)">删除</n-button>
          </div>
        </div>
      </div>
    </div>
  </n-card>
</template>