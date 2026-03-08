<script setup lang="ts">
import { NCard, NGrid, NGridItem, NButton, NSpace, NTag } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { ref } from 'vue'
import type { StoryBook } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'

const { data: books, isLoading, error } = useQuery({
  queryKey: ['books'],
  queryFn: () => get<StoryBook[]>('/story/books'),
})

const phaseOptions = [
  { label: '全部', value: 'all' },
  { label: '草稿阶段', value: 'drafting' },
  { label: '写作中', value: 'writing' },
  { label: '展示中', value: 'showcase' },
  { label: '已归档', value: 'archived' },
]

const selectedPhase = ref('all')

function getPhaseColor(phase: string) {
  const colors: Record<string, string> = {
    drafting: 'default',
    writing: 'primary',
    showcase: 'success',
    archived: 'info',
  }
  return colors[phase] || 'default'
}

function getPhaseLabel(phase: string) {
  const labels: Record<string, string> = {
    drafting: '草稿阶段',
    writing: '写作中',
    showcase: '展示中',
    archived: '已归档',
  }
  return labels[phase] || phase
}
</script>

<template>
  <div>
    <h1 class="text-3xl font-bold mb-8 text-white">故事册列表</h1>
    
    <!-- 筛选器 -->
    <n-space class="mb-6">
      <n-button
        v-for="option in phaseOptions"
        :key="option.value"
        :type="selectedPhase === option.value ? 'primary' : 'tertiary'"
        @click="selectedPhase = option.value"
      >
        {{ option.label }}
      </n-button>
    </n-space>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="text-center py-20 text-#666666">
      加载中...
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="text-center py-20 text-red-500">
      加载失败：{{ (error as Error).message }}
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="!books || books.length === 0" class="text-center py-20 text-#666666">
      暂无故事册
    </div>
    
    <!-- 故事册列表 -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <n-grid-item v-for="book in books" :key="book.id">
        <n-card
          class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors cursor-pointer"
          :content-style="{ padding: '16px' }"
        >
          <template #header>
            <div class="flex justify-between items-start">
              <h3 class="text-xl font-bold text-white truncate">{{ book.title }}</h3>
              <n-tag type="primary" size="small">
                写作中
              </n-tag>
            </div>
          </template>
          <p class="text-#a0a0a0 line-clamp-3 mb-4" style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
            {{ book.description || '暂无描述' }}
          </p>
          <div class="flex justify-between items-center">
            <span class="text-#666666 text-sm">
              创建于 {{ new Date(book.created_at).toLocaleDateString('zh-CN') }}
            </span>
            <n-button :component="RouterLink" :to="`/books/${book.id}`" type="primary" size="small">
              进入
            </n-button>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>