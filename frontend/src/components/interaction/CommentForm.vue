<script setup lang="ts">
import { NCard, NInput, NButton, NSpace } from 'naive-ui'
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCreateCommentMutation } from '@/features/interaction/queries'

const props = defineProps<{
  nodeId: number
}>()

const emits = defineEmits(['comment-added', 'require-login'])

const authStore = useAuthStore()
const content = ref('')
const { mutate: submitComment, isPending } = useCreateCommentMutation()

function handleSubmit() {
  if (!content.value.trim()) return
  submitComment(
    { nodeId: props.nodeId, payload: { content: content.value } },
    {
      onSuccess: (data) => {
        content.value = ''
        emits('comment-added', data)
      },
    }
  )
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
        <n-button type="primary" @click="handleSubmit" :loading="isPending" :disabled="isPending || !content.trim()">
          发表评论
        </n-button>
      </n-space>
    </div>
  </n-card>
</template>
