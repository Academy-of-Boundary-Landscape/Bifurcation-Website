<script setup lang="ts">
import { NCard, NButton } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, watch } from 'vue'
import type { StoryNodeTreeItem } from '@/types/models'
import StoryTreeFlow from '@/components/story/StoryTreeFlow.vue'
import StoryTreeInspector from '@/components/story/StoryTreeInspector.vue'
import StoryCreateConfirmModal from '@/components/story/StoryCreateConfirmModal.vue'
import { canCreateFromStoryNode, getStoryNodeCreationBlockedReason } from '@/features/story/creation'
import { buildStoryWriteRoute } from '@/features/story/navigation'
import { useBookQuery, useStoryTreeQuery } from '@/features/story/queries'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const bookId = computed(() => Number(route.params.bookId))
const selectedNodeId = ref<number | null>(null)
const showCreateModal = ref(false)
const focusNodeId = computed(() => {
  const rawValue = route.query.focusNodeId
  if (typeof rawValue !== 'string') {
    return null
  }

  const parsedValue = Number(rawValue)
  return Number.isFinite(parsedValue) ? parsedValue : null
})

const { data: book } = useBookQuery(bookId)
const { data: tree, isLoading: treeLoading } = useStoryTreeQuery(bookId)

function flattenTree(items: StoryNodeTreeItem[]): StoryNodeTreeItem[] {
  return items.flatMap((item) => [item, ...flattenTree(item.children ?? [])])
}

function findPath(items: StoryNodeTreeItem[], targetId: number): StoryNodeTreeItem[] {
  for (const item of items) {
    if (item.id === targetId) {
      return [item]
    }

    const childPath = findPath(item.children ?? [], targetId)
    if (childPath.length > 0) {
      return [item, ...childPath]
    }
  }

  return []
}

const flatNodes = computed(() => flattenTree(tree.value ?? []))
const totalNodes = computed(() => flatNodes.value.length)
const endingNodes = computed(() => flatNodes.value.filter((node) => node.is_ending).length)
const branchingNodes = computed(() => flatNodes.value.filter((node) => node.children.length > 1).length)
const entryNode = computed(() => tree.value?.[0] ?? null)

const selectedNode = computed(() => {
  if (selectedNodeId.value === null) {
    return entryNode.value
  }

  return flatNodes.value.find((node) => node.id === selectedNodeId.value) ?? entryNode.value
})

const selectedPath = computed(() => {
  if (!selectedNode.value) {
    return []
  }

  return findPath(tree.value ?? [], selectedNode.value.id)
})

const selectedNodePreview = computed(() => {
  const summary = selectedNode.value?.summary?.trim()
  if (summary) {
    return summary
  }

  if (selectedNode.value?.children.length) {
    return `该节点已经衍生出 ${selectedNode.value.children.length} 条后续分支，适合继续探索不同世界线。`
  }

  return '这是一个尚未展开太多描述的节点，适合作为继续阅读或创作的切入点。'
})

const canCreateFromSelectedNode = computed(() => canCreateFromStoryNode(selectedNode.value))
const selectedNodeCreationBlockedReason = computed(() => getStoryNodeCreationBlockedReason(selectedNode.value))

watch(
  () => focusNodeId.value,
  (focusedNodeId) => {
    if (focusedNodeId !== null) {
      selectedNodeId.value = focusedNodeId
    }
  },
  { immediate: true },
)

watch(
  () => tree.value,
  (nextTree) => {
    console.info('[StoryTree] tree payload received', {
      bookId: bookId.value,
      userRole: authStore.currentUser?.role ?? 'guest',
      topLevel: (nextTree ?? []).map((node) => ({
        id: node.id,
        status: node.status,
        children: node.children.length,
      })),
      totalNodes: nextTree ? flattenTree(nextTree).length : 0,
    })

    if (!nextTree || nextTree.length === 0) {
      selectedNodeId.value = null
      return
    }

    if (selectedNodeId.value === null) {
      selectedNodeId.value = nextTree[0]?.id ?? null
      return
    }

    const exists = flattenTree(nextTree).some((node) => node.id === selectedNodeId.value)
    if (!exists) {
      selectedNodeId.value = nextTree[0]?.id ?? null
    }
  },
  { immediate: true },
)

function selectNode(nodeId: number) {
  selectedNodeId.value = nodeId
}

function goToStoryNode(nodeId: number) {
  void router.push({ name: 'story-node', params: { nodeId } })
}

function requestCreateNode() {
  if (!selectedNode.value) return
  showCreateModal.value = true
}

function confirmCreateNode() {
  if (!selectedNode.value) return
  void router.push(buildStoryWriteRoute(bookId.value, selectedNode.value.id))
}
</script>

<template>
  <div class="space-y-6">
    <n-card class="ui-shell-panel overflow-hidden" :bordered="false">
      <div class="grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_300px]">
        <div class="space-y-5">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="space-y-3">
              <div class="flex items-center gap-3 flex-wrap">
                <p class="ui-shell-kicker">Story Navigation Workspace</p>
                <span class="ui-chip">
                  {{ book?.phase ?? 'drafting' }}
                </span>
              </div>
              <h1 class="ui-shell-title text-[clamp(2.4rem,4vw,4.4rem)] leading-[0.98] uppercase">
                {{ book?.title || '加载中...' }}
              </h1>
              <p class="max-w-[52rem] leading-[1.9] text-[var(--text-secondary)]">
                {{ book?.description || '这本故事册还没有补充简介。您可以先浏览世界线结构，再决定从哪个节点进入阅读。' }}
              </p>
            </div>

            <div class="grid min-w-[240px] gap-3 sm:grid-cols-3">
              <div class="ui-metric-card">
                <p class="ui-metric-card__label">节点</p>
                <p class="ui-metric-card__value">{{ totalNodes }}</p>
              </div>
              <div class="ui-metric-card">
                <p class="ui-metric-card__label">完结</p>
                <p class="ui-metric-card__value">{{ endingNodes }}</p>
              </div>
              <div class="ui-metric-card">
                <p class="ui-metric-card__label">分歧点</p>
                <p class="ui-metric-card__value">{{ branchingNodes }}</p>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap gap-3">
            <n-button
              v-if="entryNode"
              type="primary"
              @click="goToStoryNode(entryNode.id)"
            >
              从主干开始阅读
            </n-button>
            <n-button
              v-if="selectedNode"
              secondary
              type="primary"
              @click="goToStoryNode(selectedNode.id)"
            >
              查看当前节点正文
            </n-button>
            <n-button
              v-if="book?.allow_new_nodes && selectedNode"
              :disabled="!canCreateFromSelectedNode"
              @click="requestCreateNode"
            >
              创建后续节点
            </n-button>
          </div>
        </div>

        <div class="ui-panel-section p-4">
          <p class="ui-shell-kicker">Reading Guidance</p>
          <div class="mt-4 grid gap-3 text-sm leading-7 text-[var(--text-secondary)]">
            <p>拖动画布查看全局结构，缩放后点击任意节点，在右侧快速判断是否值得进入正文或继续创作。</p>
            <p>如果你刚进入这本书，先从主干或高亮节点开始读；如果你已经在某条世界线中，优先观察它的父链和兄弟分支。</p>
          </div>
        </div>
      </div>
    </n-card>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div class="min-w-0">
        <story-tree-flow :tree="tree ?? []" :selected-node-id="selectedNodeId" :is-loading="treeLoading" @node-click="selectNode" />
      </div>

      <story-tree-inspector
        :book-id="bookId"
        :book-title="book?.title"
        :allow-new-nodes="Boolean(book?.allow_new_nodes)"
        :selected-node="selectedNode"
        :selected-path="selectedPath"
        :selected-node-preview="selectedNodePreview"
        :can-create-from-selected-node="canCreateFromSelectedNode"
        :selected-node-creation-blocked-reason="selectedNodeCreationBlockedReason"
        @select-path-node="selectNode"
      />
    </div>

    <story-create-confirm-modal
      v-model:show="showCreateModal"
      :book-title="book?.title"
      :parent-node="selectedNode"
      @confirm="confirmCreateNode"
    />
  </div>
</template>
