<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ref, computed } from 'vue'
import type { StoryNodeRead } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, patch } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

// 获取待审核节点列表
const { data: pendingNodes, isLoading, refetch } = useQuery<StoryNodeRead[]>({
  queryKey: ['pending-nodes'],
  queryFn: () => get<StoryNodeRead[]>('/admin/nodes/pending'),
})

// 审核通过节点
const { mutate: approveNode, isPending: approving } = useMutation({
  mutationFn: (nodeId: number) => patch<{ detail: string }>('/admin/nodes/' + nodeId + '/audit', { status: 'published' }),
  onSuccess: (_, nodeId) => {
    message.success('节点已通过审核')
    refetch()
  },
  onError: (error) => {
    console.error('审核失败:', error)
    message.error('审核失败，请重试')
  }
})

// 审核拒绝节点
const { mutate: rejectNode, isPending: rejecting } = useMutation({
  mutationFn: ({ nodeId, reason }: { nodeId: number; reason: string }) => 
    patch<{ detail: string }>('/admin/nodes/' + nodeId + '/audit', { status: 'rejected', reject_reason: reason }),
  onSuccess: (_, variables) => {
    message.success('节点已拒绝审核')
    refetch()
  },
  onError: (error) => {
    console.error('拒绝失败:', error)
    message.error('拒绝失败，请重试')
  }
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-white mb-2">待审核节点</h1>
    <p class="text-#666666 mb-8">查看和处理待审核的创作内容</p>
    
    <!-- 筛选器 -->
    <n-card class="bg-#1a1a1a border-#2a2a2a mb-6">
      <template #header>
        <h2 class="text-xl font-bold text-white">筛选器</h2>
      </template>
      
      <div class="flex flex-wrap gap-3">
        <n-tag size="small" type="primary">全部</n-tag>
        <n-tag size="small" type="success">故事册</n-tag>
        <n-tag size="small" type="warning">分支类型</n-tag>
        <n-tag size="small" type="info">作者</n-tag>
      </div>
    </n-card>
    
    <!-- 节点列表 -->
    <n-spin :show="isLoading">
      <div v-if="!pendingNodes || pendingNodes.length === 0" class="text-center py-12">
        <div class="text-6xl mb-4">✅</div>
        <h3 class="text-xl font-bold text-white mb-2">暂无待审核节点</h3>
        <p class="text-#666666">所有节点都已处理完毕，等待新投稿</p>
      </div>
      
      <div v-else class="space-y-6">
        <n-card 
          v-for="node in pendingNodes" 
          :key="node.id" 
          class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <n-avatar 
                  :size="32" 
                  :src="node.author?.avatar"
                >
                  {{ node.author?.username?.charAt(0).toUpperCase() }}
                </n-avatar>
                <div>
                  <h3 class="text-lg font-semibold text-white">{{ node.title || node.branch_name || '无标题' }}</h3>
                  <p class="text-#666666 text-sm">{{ node.author?.username }} · {{ new Date(node.created_at).toLocaleString('zh-CN') }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <n-tag type="warning" size="small">待审核</n-tag>
                <span class="text-#666666 text-sm">{{ node.zone }}</span>
              </div>
            </div>
          </template>
          
          <!-- 正文预览 -->
          <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
            {{ node.content.substring(0, 200) }}{{ node.content.length > 200 ? '...' : '' }}
          </div>
          
          <!-- 审核操作 -->
          <div class="mt-6 pt-6 border-t border-#2a2a2a">
            <div class="flex flex-col sm:flex-row gap-3">
              <n-button 
                type="success" 
                @click="() => approveNode(node.id)"
                :loading="approving && pendingNodes.find(n => n.id === node.id)?.id === node.id"
                :disabled="approving && pendingNodes.find(n => n.id === node.id)?.id === node.id"
              >
                通过审核
              </n-button>
              
              <n-button 
                type="error" 
                @click="() => {
                  const reason = prompt('请输入拒绝原因：')
                  if (reason && reason.trim()) {
                    rejectNode({ nodeId: node.id, reason: reason.trim() })
                  }
                }"
                :loading="rejecting && pendingNodes.find(n => n.id === node.id)?.id === node.id"
                :disabled="rejecting && pendingNodes.find(n => n.id === node.id)?.id === node.id"
              >
                拒绝审核
              </n-button>
              
              <n-button 
                size="small" 
                type="primary" 
                :component="RouterLink" 
                :to="{ name: 'story-node', params: { nodeId: node.id } }"
              >
                查看详情
              </n-button>
            </div>
          </div>
        </n-card>
      </div>
    </n-spin>
  </div>
</template>
