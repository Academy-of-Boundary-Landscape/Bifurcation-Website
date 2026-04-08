<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToggleLikeMutation } from '@/features/interaction/queries'

const props = defineProps<{
  nodeId: number
  likesCount: number
  isLiked: boolean
}>()

const emits = defineEmits(['like-toggle', 'require-login'])

const authStore = useAuthStore()
const isLikedLocal = ref(props.isLiked)
const likesCountLocal = ref(props.likesCount)
const { mutate: toggleLike, isPending: loading } = useToggleLikeMutation()

// 初始化状态
onMounted(() => {
  isLikedLocal.value = props.isLiked
  likesCountLocal.value = props.likesCount
})

// 点赞/取消点赞
function handleToggle() {
  if (!authStore.isAuthenticated) {
    // 触发登录事件
    emits('require-login')
    return
  }
  
  toggleLike(
    { nodeId: props.nodeId },
    {
      onSuccess: (data) => {
        isLikedLocal.value = data.action === 'liked'
        likesCountLocal.value = data.likes_count
        emits('like-toggle', { action: data.action, likesCount: data.likes_count })
      },
    }
  )
}
</script>

<template>
  <n-button 
    :loading="loading"
    size="small"
    @click="handleToggle"
    :type="isLikedLocal ? 'primary' : 'default'"
  >
    <n-icon>
      <svg v-if="isLikedLocal" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12.1 18.55l-2.8-2.74-.02-.02L.9 7.41C.36 6.87 0 6.1 0 5.29 0 3.91 1.14 2.59 2.72 2.59h18.56c1.58 0 2.72 1.32 2.72 2.71 0 .81-.36 1.58-.9 2.12l-8.61 8.36-.02.02-2.74 2.7zm-.58-12.34H8.07l2.44 2.45z"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12c0 5.59-4.54 10-10 10a10 10 0 0 1-10-10c0-5.59 4.54-10 10-10a10 10 0 0 1 10 10z"/>
        <path d="M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/>
      </svg>
    </n-icon>
    {{ likesCountLocal }}
  </n-button>
</template>
