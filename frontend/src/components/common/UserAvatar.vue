<script setup lang="ts">
import { NAvatar } from 'naive-ui'

const props = defineProps<{
  size?: number
  src?: string
  username: string
}>()
</script>

<template>
  <n-avatar 
    :size="props.size"
    :src="props.src"
    class="cursor-pointer"
  >
    {{ props.username?.charAt(0).toUpperCase() }}
  </n-avatar>
</template>
