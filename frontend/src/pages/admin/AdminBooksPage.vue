<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ref } from 'vue'
import type { StoryBook, BookPhase } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, patch } from '@/services/http'

// 获取故事册列表
const { data: books, isLoading, refetch } = useQuery<StoryBook[]>({
  queryKey: ['books'],
  queryFn: () => get<StoryBook[]>('/story/books'),
})

// 更新故事册状态
const { mutate: updateBook, isPending: updating } = useMutation({
  mutationFn: ({ bookId, phase }: { bookId: number; phase: BookPhase }) => 
    patch<StoryBook>(`/story/books/${bookId}`, { phase }),
  onSuccess: (_, variables) => {
    // 更新缓存中的对应故事册
    if (books.value) {
      const bookIndex = books.value.findIndex(b => b.id === variables.bookId)
      if (bookIndex !== -1) {
        const book = books.value[bookIndex]
        if (book) {
          book.phase = variables.phase
        }
      }
    }
    refetch()
  },
  onError: (error) => {
    console.error('更新失败:', error)
  }
})

function getPhaseType(phase: BookPhase) {
  switch (phase) {
    case 'drafting':
      return 'warning'
    case 'writing':
      return 'primary'
    case 'showcase':
      return 'success'
    case 'archived':
      return 'default'
  }
}

function getPhaseLabel(phase: BookPhase) {
  switch (phase) {
    case 'drafting':
      return '草稿阶段'
    case 'writing':
      return '写作中'
    case 'showcase':
      return '展示中'
    case 'archived':
      return '已归档'
  }
}

function updateBookPhase(bookId: number, phase: BookPhase) {
  updateBook({ bookId, phase })
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-white mb-2">故事册管理</h1>
    <p class="text-#666666 mb-8">管理故事册的状态和阶段</p>
    
    <!-- 筛选器 -->
    <n-card class="bg-#1a1a1a border-#2a2a2a mb-6">
      <template #header>
        <h2 class="text-xl font-bold text-white">筛选器</h2>
      </template>
      
      <div class="flex flex-wrap gap-3">
        <n-tag size="small" type="primary">全部</n-tag>
        <n-tag size="small" type="success">草稿阶段</n-tag>
        <n-tag size="small" type="warning">写作中</n-tag>
        <n-tag size="small" type="info">展示中</n-tag>
      </div>
    </n-card>
    
    <!-- 故事册列表 -->
    <n-spin :show="isLoading">
      <div v-if="!books || books.length === 0" class="text-center py-12">
        <div class="text-6xl mb-4">📚</div>
        <h3 class="text-xl font-bold text-white mb-2">暂无故事册</h3>
        <p class="text-#666666">当前没有创建任何故事册，请先创建</p>
      </div>
      
      <div v-else class="space-y-6">
        <n-card 
          v-for="book in books" 
          :key="book.id" 
          class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white">
                  📚
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-white">{{ book.title }}</h3>
                  <p class="text-#666666 text-sm">{{ book.description?.substring(0, 50) }}{{ (book.description?.length ?? 0) > 50 ? '...' : '' }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <n-tag :type="getPhaseType(book.phase)" size="small">{{ getPhaseLabel(book.phase) }}</n-tag>
                <span class="text-#666666 text-sm">{{ book.created_at ? new Date(book.created_at).toLocaleDateString('zh-CN') : '-' }}</span>
              </div>
            </div>
          </template>
          
          <!-- 故事册信息 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div class="space-y-2">
              <p class="text-#666666 text-sm">开放状态:</p>
              <n-tag 
                :type="book.is_active ? 'success' : 'error'" 
                size="small"
              >
                {{ book.is_active ? '已开放' : '未开放' }}
              </n-tag>
            </div>
            
            <div class="space-y-2">
              <p class="text-#666666 text-sm">节点总数:</p>
              <span class="text-white">{{ book.nodes_count || 0 }}</span>
            </div>
            
            <div class="space-y-2">
              <p class="text-#666666 text-sm">最后更新:</p>
              <span class="text-white">{{ book.updated_at ? new Date(book.updated_at).toLocaleString('zh-CN') : '-' }}</span>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="mt-4 pt-4 border-t border-#2a2a2a">
            <div class="flex flex-col sm:flex-row gap-3">
              <n-button 
                type="primary" 
                :component="RouterLink" 
                :to="{ name: 'book-detail', params: { bookId: book.id } }"
              >
                查看详情
              </n-button>
              
              <n-button 
                v-if="book.phase !== 'drafting'" 
                type="default" 
                @click="updateBookPhase(book.id, 'drafting')"
                :loading="updating && books.find(b => b.id === book.id)?.id === book.id"
                :disabled="updating && books.find(b => b.id === book.id)?.id === book.id"
              >
                设为草稿
              </n-button>
              
              <n-button 
                v-if="book.phase !== 'writing'" 
                type="primary" 
                @click="updateBookPhase(book.id, 'writing')"
                :loading="updating && books.find(b => b.id === book.id)?.id === book.id"
                :disabled="updating && books.find(b => b.id === book.id)?.id === book.id"
              >
                开启写作
              </n-button>
              
              <n-button 
                v-if="book.phase !== 'showcase'" 
                type="success" 
                @click="updateBookPhase(book.id, 'showcase')"
                :loading="updating && books.find(b => b.id === book.id)?.id === book.id"
                :disabled="updating && books.find(b => b.id === book.id)?.id === book.id"
              >
                展示发布
              </n-button>
            </div>
          </div>
        </n-card>
      </div>
    </n-spin>
  </div>
</template>
