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

// 给 StoryTreeFlow 用的 ID 列表（避免组件深拷贝整棵树）
const selectedPathIds = computed(() => selectedPath.value.map((node) => node.id))

// 面包屑显示用：每个节点取 branch_name → title → 占位
function getBreadcrumbLabel(node: StoryNodeTreeItem) {
  const label = (node.branch_name || node.title || '').trim()
  return label || `节点 ${node.id}`
}

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

          <!-- 选中节点指示条：让"现在选中了什么"明确，方便快速续写 -->
          <div
            v-if="selectedNode"
            class="mt-1 flex flex-wrap items-baseline gap-3 px-3 py-2 border border-[var(--line-faint)] bg-[var(--bg-shell)]"
          >
            <span class="font-mono text-[0.7rem] tracking-[0.22em] uppercase text-[var(--text-faint)]">
              SELECTED
            </span>
            <span class="font-mono text-[0.85rem] text-[var(--text-secondary)]">
              NODE-{{ selectedNode.id }}
            </span>
            <span class="text-[0.92rem] text-[var(--text-primary)] truncate max-w-[28rem]">
              {{ selectedNode.title || selectedNode.branch_name || '未命名节点' }}
            </span>
          </div>

          <!-- 主操作行：选中节点之后，"续写"是首要动作 -->
          <div class="flex flex-wrap gap-3">
            <!-- 续写：选中节点后变成最显眼的主按钮 -->
            <n-button
              v-if="book?.allow_new_nodes && selectedNode"
              type="primary"
              size="large"
              :disabled="!canCreateFromSelectedNode"
              @click="requestCreateNode"
            >
              从此处续写 →
            </n-button>
            <!-- 阅读选中节点：次级 -->
            <n-button
              v-if="selectedNode"
              secondary
              type="primary"
              @click="goToStoryNode(selectedNode.id)"
            >
              阅读选中节点
            </n-button>
            <!-- 主干阅读：选中节点时降级为 quaternary，未选中时仍为 primary 入口 -->
            <n-button
              v-if="entryNode"
              :type="selectedNode ? undefined : 'primary'"
              :quaternary="!!selectedNode"
              @click="goToStoryNode(entryNode.id)"
            >
              {{ selectedNode ? '从主干开始阅读' : '进入主干' }}
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
      <div class="min-w-0 space-y-3">
        <!-- 面包屑路径条（方案 2）：选中节点深度 > 1 才显示 -->
        <nav
          v-if="selectedPath.length > 1"
          class="tree-lineage"
          aria-label="从根到选中节点的路径"
        >
          <span class="tree-lineage__head">LINEAGE</span>
          <ol class="tree-lineage__list">
            <li
              v-for="(pathNode, idx) in selectedPath"
              :key="`crumb-${pathNode.id}`"
              class="tree-lineage__item"
              :class="{ 'tree-lineage__item--current': idx === selectedPath.length - 1 }"
            >
              <button
                type="button"
                class="tree-lineage__link"
                :disabled="idx === selectedPath.length - 1"
                :aria-current="idx === selectedPath.length - 1 ? 'true' : undefined"
                @click="selectNode(pathNode.id)"
              >
                <span v-if="idx === 0" class="tree-lineage__rank">ROOT</span>
                <span v-else class="tree-lineage__rank">L{{ idx }}</span>
                <span class="tree-lineage__label">{{ getBreadcrumbLabel(pathNode) }}</span>
              </button>
              <span
                v-if="idx < selectedPath.length - 1"
                class="tree-lineage__sep"
                aria-hidden="true"
              >→</span>
            </li>
          </ol>
        </nav>

        <story-tree-flow
          :tree="tree ?? []"
          :selected-node-id="selectedNodeId"
          :selected-path-ids="selectedPathIds"
          :is-loading="treeLoading"
          @node-click="selectNode"
        />
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

<style scoped>
/* —— 面包屑：从根到选中节点的路径（方案 2）—— */
.tree-lineage {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border: 1px solid var(--line-faint);
  background: var(--bg-shell);
  overflow-x: auto;
  scrollbar-width: thin;
}

.tree-lineage__head {
  flex: 0 0 auto;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--text-faint);
  padding-right: 12px;
  border-right: 1px solid var(--line-faint);
}

.tree-lineage__list {
  display: flex;
  align-items: center;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
  flex-wrap: nowrap;
}

.tree-lineage__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.tree-lineage__link {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  background: none;
  border: 0;
  padding: 4px 6px;
  font-family: var(--font-body);
  font-size: 0.86rem;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 2px;
  transition: color var(--transition-base), background var(--transition-base);
  white-space: nowrap;
}

.tree-lineage__link:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--bg-panel);
}

.tree-lineage__link:disabled {
  cursor: default;
}

.tree-lineage__rank {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.tree-lineage__label {
  color: inherit;
  max-width: 18ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-lineage__item--current .tree-lineage__link {
  color: var(--text-primary);
  font-weight: 500;
}

.tree-lineage__item--current .tree-lineage__rank {
  color: var(--text-secondary);
}

.tree-lineage__sep {
  font-family: var(--font-mono);
  font-size: 0.86rem;
  color: var(--text-faint);
  user-select: none;
}
</style>
