<script setup lang="ts">
import { NCard, NButton } from 'naive-ui'

const props = defineProps<{
  content: string
  title?: string
  branchName?: string
}>()
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <h2 class="text-xl font-bold text-white">预览</h2>
      <p class="text-#666666 text-sm mt-1">查看您的创作效果</p>
    </template>
    
    <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
      <h3 v-if="props.title" class="text-lg font-semibold text-white">{{ props.title }}</h3>
      <h4 v-if="props.branchName" class="text-md font-medium text-white">{{ props.branchName }}</h4>
      <p>{{ props.content }}</p>
    </div>
    
    <div class="mt-6 flex justify-end">
      <n-button @click="$emit('close')">
        关闭预览
      </n-button>
    </div>
  </n-card>
</template>