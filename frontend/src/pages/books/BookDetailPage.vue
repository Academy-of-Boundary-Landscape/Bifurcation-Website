<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem } from 'naive-ui'
import { RouterLink, useRoute } from 'vue-router'
import { computed } from 'vue'
import type { StoryBook, StoryNodeTreeItem } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'

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
          <n-button :component="RouterLink" :to="`/story/lineage/`" type="primary">
            开始阅读
          </n-button>
          <n-button :component="RouterLink" :to="`/story/write/${bookId}?mode=continue`" variant="outline">
            我要续写
          </n-button>
        </n-space>
      </n-card>
      
      <!-- 树状展示区 -->
      <n-card class="bg-#1a1a1a border-#2a2a2a">
        <template #header>
          <h2 class="text-xl font-bold text-white">故事树</h2>
        </template>
        
        <n-spin :show="treeLoading">
          <div v-if="!tree || tree.length === 0" class="text-center py-10 text-#666666">
            暂无节点，成为第一个创作者吧！
          </div>
          
          <n-timeline v-else>
            <n-timeline-item
              v-for="node in tree"
              :key="node.id"
              :title="node.branch_name || node.title || '无标题'"
              :content="node.summary"
              :time="new Date(node.created_at).toLocaleDateString('zh-CN')"
            >
              <template #header>
                <div class="flex justify-between items-center">
                  <span class="text-white">{{ node.author?.username }}</span>
                  <n-space>
                    <span class="text-#666666 text-sm">👍 {{ node.likes_count }}</span>
                    <n-button
                      :component="RouterLink"
                      :to="`/story/node/${node.id}`"
                      size="small"
                      type="primary"
                    >
                      查看
                    </n-button>
                  </n-space>
                </div>
              </template>
            </n-timeline-item>
          </n-timeline>
        </n-spin>
      </n-card>
    </n-space>
  </div>
</template>