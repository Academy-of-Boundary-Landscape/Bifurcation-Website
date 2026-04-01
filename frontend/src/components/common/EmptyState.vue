<script setup lang="ts">
import { NCard, NButton } from 'naive-ui'
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a text-center py-12">
    <div class="text-6xl mb-4">📖</div>
    <h3 class="text-xl font-bold text-white mb-2">{{ title }}</h3>
    <p class="text-#666666 mb-6">{{ description }}</p>
    <n-button v-if="showButton" type="primary" @click="$emit('action')">
      {{ buttonText }}
    </n-button>
  </n-card>
</template>

<script lang="ts">
export default {
  name: 'EmptyState',
  props: {
    title: {
      type: String,
      default: '暂无内容',
    },
    description: {
      type: String,
      default: '当前页面还没有任何内容',
    },
    showButton: {
      type: Boolean,
      default: false,
    },
    buttonText: {
      type: String,
      default: '去添加',
    }
  },
  emits: ['action']
}
</script>