<script setup lang="ts">
import { NCard, NButton, NDivider } from 'naive-ui'
import { useRouter } from 'vue-router'
import { ref } from 'vue'
import type { StoryNodeTreeItem } from '@/types/models'
import StoryCreateConfirmModal from '@/components/story/StoryCreateConfirmModal.vue'
import { buildStoryWriteRoute } from '@/features/story/navigation'

const router = useRouter()
const showCreateModal = ref(false)
const props = defineProps<{
  bookId: number
  bookTitle?: string | null
  allowNewNodes: boolean
  selectedNode: StoryNodeTreeItem | null
  selectedPath: StoryNodeTreeItem[]
  selectedNodePreview: string
  canCreateFromSelectedNode: boolean
  selectedNodeCreationBlockedReason: string
}>()

const emit = defineEmits<{
  selectPathNode: [nodeId: number]
}>()

function handleSelectPathNode(nodeId: number) {
  emit('selectPathNode', nodeId)
}

function openNode(nodeId: number) {
  void router.push({ name: 'story-node', params: { nodeId } })
}

function requestCreateChildNode() {
  if (!props.selectedNode) return
  showCreateModal.value = true
}

function requestCreateFirstNode() {
  showCreateModal.value = true
}

function confirmCreateNode() {
  void router.push(buildStoryWriteRoute(props.bookId, props.selectedNode?.id))
}
</script>

<template>
  <n-card class="ui-shell-panel h-fit sticky top-6" :bordered="false">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="ui-shell-kicker">Node Inspector</p>
          <h2 class="ui-shell-title mt-2 text-[1.4rem] uppercase">
            {{ selectedNode?.branch_name || selectedNode?.title || '作品概览' }}
          </h2>
        </div>
        <span v-if="selectedNode" class="ui-chip">
          {{ selectedNode.is_ending ? '已完结' : selectedNode.status }}
        </span>
      </div>
    </template>

    <div v-if="selectedNode" class="space-y-5">
      <div class="ui-panel-section p-4">
        <p class="ui-panel-section__label">摘要预览</p>
        <p class="mt-3 leading-[1.85] text-[var(--text-primary)]">
          {{ selectedNodePreview }}
        </p>
      </div>

      <div class="grid gap-3 sm:grid-cols-2">
        <div class="ui-metric-card">
          <p class="ui-metric-card__label">作者</p>
          <p class="ui-metric-card__value text-[1.15rem]">{{ selectedNode.author?.username || '未知作者' }}</p>
        </div>
        <div class="ui-metric-card">
          <p class="ui-metric-card__label">创建时间</p>
          <p class="ui-metric-card__value text-[1.15rem]">{{ new Date(selectedNode.created_at).toLocaleDateString('zh-CN') }}</p>
        </div>
        <div class="ui-metric-card">
          <p class="ui-metric-card__label">点赞</p>
          <p class="ui-metric-card__value text-[1.15rem]">{{ selectedNode.likes_count }}</p>
        </div>
        <div class="ui-metric-card">
          <p class="ui-metric-card__label">子分支</p>
          <p class="ui-metric-card__value text-[1.15rem]">{{ selectedNode.children.length }}</p>
        </div>
      </div>

      <div>
        <p class="ui-panel-section__label">当前路径</p>
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <template v-for="(node, index) in selectedPath" :key="node.id">
            <button
              type="button"
              class="border-0 bg-transparent p-0 text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
              @click="handleSelectPathNode(node.id)"
            >
              {{ node.branch_name || node.title || `节点${node.id}` }}
            </button>
            <span v-if="index < selectedPath.length - 1" class="text-[var(--text-faint)]">/</span>
          </template>
        </div>
      </div>

      <n-divider class="!my-0" />

      <div class="grid gap-3">
        <n-button type="primary" block @click="openNode(selectedNode.id)">
          查看正文
        </n-button>
        <n-button
          v-if="allowNewNodes"
          block
          :disabled="!canCreateFromSelectedNode"
          @click="requestCreateChildNode"
        >
          创建后续节点
        </n-button>
      </div>

      <p
        v-if="allowNewNodes && selectedNodeCreationBlockedReason"
        class="text-sm leading-7 text-[var(--text-muted)]"
      >
        {{ selectedNodeCreationBlockedReason }}
      </p>
    </div>

    <div v-else class="space-y-4 text-[var(--text-secondary)]">
      <p>这本书还没有任何节点。等第一位创作者落笔之后，这里会成为整个故事树的导航台。</p>
      <n-button v-if="allowNewNodes" type="primary" block @click="requestCreateFirstNode">
        创建第一个节点
      </n-button>
    </div>
  </n-card>

  <story-create-confirm-modal
    v-model:show="showCreateModal"
    :book-title="bookTitle"
    :parent-node="selectedNode"
    @confirm="confirmCreateNode"
  />
</template>
