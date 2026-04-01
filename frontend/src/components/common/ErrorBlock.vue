<script setup lang="ts">
import { NCard, NButton } from 'naive-ui'
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a text-center py-12">
    <div class="text-6xl mb-4">⚠️</div>
    <h3 class="text-xl font-bold text-white mb-2">{{ title }}</h3>
    <p class="text-#666666 mb-6">{{ description }}</p>
    <n-button type="primary" @click="$emit('retry')">
      {{ buttonText }}
    </n-button>
  </n-card>
</template>

<script lang="ts">
export default {
  name: 'ErrorBlock',
  props: {
    title: {
      type: String,
      default: '加载失败',
    },
    description: {
      type: String,
      default: '无法加载内容，请检查网络连接',
    },
    buttonText: {
      type: String,
      default: '重试',
    }
  },
  emits: ['retry']
}
</script>