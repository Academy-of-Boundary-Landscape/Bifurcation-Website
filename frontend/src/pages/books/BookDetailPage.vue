<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin } from 'naive-ui'
import { RouterLink, useRoute } from 'vue-router'
import { computed } from 'vue'
import type { StoryBook, StoryNodeTreeItem } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'
import StoryTreePanel from '@/components/story/StoryTreePanel.vue'
import StoryTreeFlow from '@/components/story/StoryTreeFlow.vue'

const route = useRoute()
const bookId = computed(() => Number(route.params.bookId))

const { data: book, isLoading: bookLoading } = useQuery<StoryBook>({
  queryKey: ['book', bookId],
  queryFn: () => {
    // 注意：后端可能需要单独的接口获取单个 book 详情
    // 这里先使用列表接口模拟
    return get<StoryBook>(`/story/books/${bookId.value}`)
  },
})

const { data: tree, isLoading: treeLoading } = useQuery<StoryNodeTreeItem[]>({
  queryKey: ['story-tree', bookId],
  queryFn: () => get<StoryNodeTreeItem[]>(`/story/tree?book_id=${bookId.value}`),
})
</script>

<template>
  <div>
    <n-space vertical>
      <!-- 故事册头部信息 -->
      <n-card class="bg-#1a1a1a border-#2a2a2a">
        <template #header>
          <div class="flex justify-between items-center">
            <h1 class="text-3xl font-bold text-white">
              {{ book?.title || '加载中...' }}
            </h1>
            <n-tag type="primary">写作中</n-tag>
          </div>
        </template>
        
        <p class="text-#a0a0a0 mb-4">
          {{ book?.description || '暂无描述' }}
        </p>
        
        <n-space>
          <n-button 
            :component="RouterLink" 
            :to="`/story/lineage/${tree?.[0]?.id}`" 
            type="primary"
            v-if="tree && tree.length > 0"
          >
            开始阅读
          </n-button>
          <n-button 
            :component="RouterLink" 
            :to="`/story/write/${bookId}?mode=continue`" 
            variant="outline"
            v-if="book?.allow_new_nodes"
          >
            我要续写
          </n-button>
        </n-space>
      </n-card>
      
      <!-- 树状展示区（Vue Flow 版本） -->
      <story-tree-flow :tree="tree ?? []" />
    </n-space>
  </div>
</template>
