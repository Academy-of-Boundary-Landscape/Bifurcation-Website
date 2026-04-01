<script setup lang="ts">
import { NSpin, NCard } from 'naive-ui'
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a flex items-center justify-center py-12">
    <n-spin size="large" />
    <div class="text-white mt-4">{{ message }}</div>
  </n-card>
</template>

<script lang="ts">
export default {
  name: 'LoadingBlock',
  props: {
    message: {
      type: String,
      default: '加载中...',
    }
  }
}
</script>