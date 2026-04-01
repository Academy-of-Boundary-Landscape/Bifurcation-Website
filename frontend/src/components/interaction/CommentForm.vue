<script setup lang="ts">
import { NCard, NInput, NButton, NSpace } from 'naive-ui'
import { ref, computed } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { post } from '@/services/http'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  nodeId: number
}>()

const emits = defineEmits(['comment-added', 'require-login'])

const authStore = useAuthStore()
const queryClient = useQueryClient()
const content = ref('')
const loading = ref(false)

// 提交评论
const { mutate: submitComment } = useMutation({
  mutationFn: () => post(`/interaction/node/${props.nodeId}/comment`, { content: content.value }),
  onSuccess: (data) => {
    content.value = ''
    emits('comment-added', data)
    
    // 更新缓存
    queryClient.invalidateQueries({ queryKey: ['node-comments', props.nodeId] })
  }
})

function handleSubmit() {
  if (!content.value.trim()) return
  
  loading.value = true
  submitComment()
}
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <h3 class="text-lg font-bold text-white">发表评论</h3>
    </template>
    
    <div v-if="!authStore.isAuthenticated" class="py-4">
      <p class="text-#666666">请先登录才能发表评论</p>
      <n-button type="primary" @click="$emit('require-login')">立即登录</n-button>
    </div>
    
    <div v-else>
      <n-input 
        v-model:value="content" 
        type="textarea"
        placeholder="写下你的评论..."
        :rows="3"
        class="mb-4"
      />
      <n-space>
        <n-button type="primary" @click="handleSubmit" :loading="loading" :disabled="loading || !content.trim()">
          发表评论
        </n-button>
      </n-space>
    </div>
  </n-card>
</template>