<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar, NDivider } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import { useNodeDetailQuery, useNodeLineageQuery } from '@/features/story/queries'
import { useToggleLikeMutation } from '@/features/interaction/queries'
import StoryCreateConfirmModal from '@/components/story/StoryCreateConfirmModal.vue'
import { buildStoryWriteRoute } from '@/features/story/navigation'
import { storyStatusLabel } from '@/utils/storyStatus'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const nodeId = computed(() => Number(route.params.nodeId))
const showCreateModal = ref(false)

const { data: node, isLoading } = useNodeDetailQuery(nodeId)
const { data: lineage } = useNodeLineageQuery(nodeId)
const { mutate: toggleLike, isPending: togglingLike } = useToggleLikeMutation()

function handleToggleLike(targetNodeId: number) {
  toggleLike(
    { nodeId: targetNodeId, bookId: node.value?.book_id },
    {
      onSuccess: (data) => {
        message.success(data.action === 'liked' ? '点赞成功' : '已取消点赞')
      },
      onError: () => {
        message.error('操作失败，请重试')
      },
    }
  )
}

function handleCreateChildNode() {
  if (!authStore.isAuthenticated) {
    void router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  showCreateModal.value = true
}

function confirmCreateChildNode() {
  if (!node.value) return
  void router.push(buildStoryWriteRoute(node.value.book_id, nodeId.value))
}

function handleBackToTree() {
  if (!node.value) return
  void router.push({ name: 'book-detail', params: { bookId: node.value.book_id }, query: { focusNodeId: node.value.id } })
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <n-spin :show="isLoading">
      <!-- 路径导航 -->
      <n-card v-if="lineage && lineage.length > 0" class="bg-#1a1a1a border-#2a2a2a mb-6">
        <div class="flex items-center flex-wrap gap-2">
          <span class="text-#666666">当前分支:</span>
          <template v-for="(item, index) in lineage" :key="item.id">
            <router-link 
              :to="{ name: 'story-node', params: { nodeId: item.id } }" 
              class="text-#8b5cf6 hover:underline"
              :class="index === lineage.length - 1 ? 'font-bold text-white' : ''"
            >
              {{ item.branch_name || item.title || `节点${item.id}` }}
            </router-link>
            <span v-if="index < lineage.length - 1" class="text-#666666">→</span>
          </template>
        </div>
        <div v-if="node" class="mt-4 flex justify-end">
          <n-button size="small" @click="handleBackToTree">
            返回故事树
          </n-button>
        </div>
      </n-card>

      <!-- 完整分支阅读区 -->
      <div v-if="lineage" class="space-y-8">
        <template v-for="(item, index) in lineage" :key="item.id">
          <n-card 
            class="bg-#1a1a1a border-#2a2a2a transition-all duration-300"
            :class="index === lineage.length - 1 ? 'ring-2 ring-#8b5cf6 scale-[1.02]' : 'hover:shadow-lg hover:border-#3a3a3a'"
          >
            <div class="flex justify-between items-start mb-4">
              <div>
                <h2 class="text-xl font-bold text-white mb-2">
                  {{ item.title || item.branch_name || '无标题' }}
                </h2>
                <div class="flex items-center gap-4 text-#666666">
                  <n-avatar 
                    :size="32" 
                    :src="item.author?.avatar ?? undefined"
                  >
                    {{ item.author?.username?.charAt(0).toUpperCase() }}
                  </n-avatar>
                  <span>{{ item.author?.username }}</span>
                  <span>{{ new Date(item.created_at).toLocaleDateString('zh-CN') }}</span>
                  <n-tag :type="item.status === 'published' ? 'success' : 'warning'">
                    {{ storyStatusLabel(item.status) }}
                  </n-tag>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-sm text-#666666">第 {{ index + 1 }} 节</span>
                <span class="text-sm text-#666666">·</span>
                <span class="text-sm text-#666666">{{ item.likes_count || 0 }} 赞</span>
              </div>
            </div>
            
            <!-- 正文内容 -->
            <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
              {{ item.content }}
            </div>
            
            <!-- 操作按钮 -->
            <div class="mt-4 pt-4 border-t border-#2a2a2a">
              <n-space>
                <n-button size="small" type="primary" @click="handleToggleLike(item.id)" :loading="togglingLike && item.id === nodeId">
                  👍 {{ item.likes_count || 0 }} 赞
                </n-button>
                <n-button size="small" @click="$router.push({ name: 'story-node', params: { nodeId: item.id } })">
                  查看详情
                </n-button>
                <n-button v-if="index === lineage.length - 1" size="small" @click="handleCreateChildNode">
                  创建后续节点
                </n-button>
              </n-space>
            </div>
          </n-card>
        </template>
      </div>

      <!-- 空状态 -->
      <div v-if="!lineage || lineage.length === 0" class="text-center py-16">
        <div class="text-6xl mb-4">📖</div>
        <h2 class="text-2xl font-bold text-white mb-2">暂无完整分支</h2>
        <p class="text-#666666">该节点尚未形成完整的分支路径，无法查看完整阅读体验</p>
        
        <div class="mt-8">
          <n-button 
            type="primary" 
            size="large" 
            @click="$router.push({ name: 'books' })"
          >
            查看故事册
          </n-button>
        </div>
      </div>

      <story-create-confirm-modal
        v-if="node"
        v-model:show="showCreateModal"
        :book-title="null"
        :parent-node="node"
        @confirm="confirmCreateChildNode"
      />
    </n-spin>
  </div>
</template>
