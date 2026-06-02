<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NAvatar, NButton, NEmpty, NInput, NSelect, NSpin, NTag } from 'naive-ui'
import { useMessage } from 'naive-ui'

import { useAdminNodesQuery, useAuditStoryNodeMutation } from '@/features/admin/queries'
import type { NodeStatus } from '@/types/models'
import { storyStatusLabel } from '@/utils/storyStatus'

const message = useMessage()
const router = useRouter()

const filters = reactive<{
  status?: NodeStatus
  keyword?: string
  limit: number
}>({
  status: undefined,
  keyword: undefined,
  limit: 80,
})

const { data: adminNodes, isLoading } = useAdminNodesQuery(computed(() => ({
  limit: filters.limit,
  status: filters.status,
  keyword: filters.keyword?.trim() || undefined,
})))
const { mutate: auditNode, isPending: auditing } = useAuditStoryNodeMutation()

const activeNodeId = ref<number | null>(null)
const expandedNodeId = ref<number | null>(null)
const nodeTargetStatus = ref<Record<number, 'published' | 'archived'>>({})
const nodeReason = ref<Record<number, string>>({})

const statusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '待审核', value: 'pending' },
  { label: '已发布', value: 'published' },
  { label: '已归档', value: 'archived' },
]

const actionOptions = [
  { label: '设为已发布', value: 'published' },
  { label: '设为已归档', value: 'archived' },
]

const totalNodes = computed(() => adminNodes.value?.length ?? 0)
const pendingCount = computed(() => adminNodes.value?.filter((node) => node.status === 'pending').length ?? 0)
const archivedCount = computed(() => adminNodes.value?.filter((node) => node.status === 'archived').length ?? 0)

function formatDateTime(value: string | null | undefined) {
  if (!value) return '-'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '-'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed)
}

function statusTagType(status: NodeStatus) {
  if (status === 'published') return 'success'
  if (status === 'archived') return 'error'
  return 'warning'
}

function getActionStatus(nodeId: number, currentStatus: NodeStatus) {
  return nodeTargetStatus.value[nodeId] ?? (currentStatus === 'archived' ? 'published' : 'archived')
}

function setActionStatus(nodeId: number, value: 'published' | 'archived') {
  nodeTargetStatus.value = {
    ...nodeTargetStatus.value,
    [nodeId]: value,
  }
}

function getReason(nodeId: number) {
  return nodeReason.value[nodeId] || ''
}

function setReason(nodeId: number, value: string) {
  nodeReason.value = {
    ...nodeReason.value,
    [nodeId]: value,
  }
}

function toggleExpanded(nodeId: number) {
  expandedNodeId.value = expandedNodeId.value === nodeId ? null : nodeId
}

function openNodeDetail(nodeId: number) {
  void router.push({ name: 'story-node', params: { nodeId } })
}

function focusNodeTree(node: { id: number; book_id: number }) {
  void router.push({ name: 'book-detail', params: { bookId: node.book_id }, query: { focusNodeId: node.id } })
}

function handleApply(nodeId: number, currentStatus: NodeStatus) {
  const nextStatus = getActionStatus(nodeId, currentStatus)
  const reason = getReason(nodeId).trim()

  if (nextStatus === 'archived' && !reason) {
    message.error('归档时请填写原因')
    return
  }

  activeNodeId.value = nodeId
  auditNode(
    {
      nodeId,
      payload: nextStatus === 'archived'
        ? { status: 'archived', reject_reason: reason }
        : { status: 'published' },
    },
    {
      onSuccess: () => {
        message.success(nextStatus === 'published' ? '节点已发布' : '节点已归档')
        nodeReason.value = {
          ...nodeReason.value,
          [nodeId]: '',
        }
        nodeTargetStatus.value = {
          ...nodeTargetStatus.value,
          [nodeId]: nextStatus === 'published' ? 'archived' : 'published',
        }
      },
      onError: () => {
        message.error('状态更新失败，请重试')
      },
      onSettled: () => {
        activeNodeId.value = null
      },
    },
  )
}
</script>

<template>
  <div class="ui-page-stack admin-page">
    <section class="ui-page-hero ui-shell-panel ui-shell-grid">
      <div class="ui-page-hero__grid admin-hero">
        <div>
          <p class="ui-shell-kicker">Admin / Nodes</p>
          <h1 class="ui-shell-title">节点管理工作台</h1>
          <p class="ui-page-hero__lead">
            这里不只处理待审核投稿，也用于查看和管理已发布、已归档节点。管理员应当能直接定位任何节点，而不是被迫回到故事树里盲找。
          </p>
        </div>
        <div class="admin-hero__metrics">
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">当前结果</p>
            <p class="ui-metric-card__value">{{ totalNodes }}</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">待审核</p>
            <p class="ui-metric-card__value">{{ pendingCount }}</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">已归档</p>
            <p class="ui-metric-card__value">{{ archivedCount }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Filters</p>
          <h2 class="ui-shell-title">筛选节点</h2>
          <p class="ui-page-section__lead">按状态和关键词缩小范围，快速定位根节点、作者自己的归档节点或待审核投稿。</p>
        </div>
      </div>

      <div class="admin-filters ui-panel-section">
        <n-select
          :value="filters.status ?? 'all'"
          class="admin-filters__status"
          :options="statusOptions"
          @update:value="filters.status = $event === 'all' ? undefined : $event"
        />
        <n-input
          :value="filters.keyword ?? ''"
          placeholder="搜索标题、分支名或摘要"
          clearable
          @update:value="filters.keyword = $event || undefined"
        />
        <n-button secondary @click="filters.status = 'pending'">
          只看待审核
        </n-button>
        <n-button secondary @click="filters.status = 'archived'">
          只看已归档
        </n-button>
        <n-button tertiary @click="filters.status = undefined; filters.keyword = undefined">
          清空筛选
        </n-button>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Node List</p>
          <h2 class="ui-shell-title">管理列表</h2>
          <p class="ui-page-section__lead">直接查看正文、切换状态，或跳回故事树聚焦某个节点。</p>
        </div>
      </div>

      <n-spin :show="isLoading">
        <n-empty v-if="!adminNodes?.length" description="当前筛选条件下没有节点" />

        <div v-else class="audit-list">
          <article
            v-for="node in adminNodes"
            :key="node.id"
            class="audit-card ui-panel-section"
          >
            <div class="audit-card__header">
              <div class="audit-card__author">
                <n-avatar :size="40" :src="node.author?.avatar ?? undefined">
                  {{ node.author?.username?.charAt(0).toUpperCase() }}
                </n-avatar>
                <div>
                  <h3 class="audit-card__title">{{ node.title || node.branch_name || '无标题节点' }}</h3>
                  <p class="audit-card__meta">
                    {{ node.author?.username || '未知作者' }} · {{ formatDateTime(node.created_at) }}
                  </p>
                </div>
              </div>

              <div class="audit-card__badges">
                <n-tag size="small" :type="statusTagType(node.status)">{{ storyStatusLabel(node.status) }}</n-tag>
                <n-tag size="small" type="default">Book {{ node.book_id }}</n-tag>
                <n-tag size="small" type="default">Node {{ node.id }}</n-tag>
                <n-tag size="small" type="default">{{ node.word_count }} 字</n-tag>
              </div>
            </div>

            <div class="audit-card__section">
              <p class="audit-card__label">摘要</p>
              <p class="audit-card__summary">{{ node.summary || '作者未填写摘要。' }}</p>
            </div>

            <div class="audit-card__section">
              <p class="audit-card__label">正文预览</p>
              <div class="audit-card__content">
                {{ expandedNodeId === node.id ? node.content : `${node.content.slice(0, 320)}${node.content.length > 320 ? '...' : ''}` }}
              </div>
              <div class="audit-card__text-actions">
                <n-button size="small" tertiary @click="toggleExpanded(node.id)">
                  {{ expandedNodeId === node.id ? '收起正文' : '展开正文' }}
                </n-button>
                <n-button size="small" @click="focusNodeTree(node)">
                  在树中定位
                </n-button>
                <n-button size="small" type="primary" @click="openNodeDetail(node.id)">
                  查看详情页
                </n-button>
              </div>
            </div>

            <div class="audit-card__section audit-card__admin">
              <div class="audit-card__admin-head">
                <p class="audit-card__label">状态管理</p>
                <p class="audit-card__hint">审核流只支持发布或归档；`pending` 仅用于用户投稿后的待审核状态。</p>
              </div>

              <div class="audit-card__admin-controls">
                <n-select
                  :value="getActionStatus(node.id, node.status)"
                  size="small"
                  class="audit-card__admin-select"
                  :options="actionOptions"
                  @update:value="setActionStatus(node.id, $event)"
                />
                <n-button
                  size="small"
                  type="primary"
                  :loading="auditing && activeNodeId === node.id"
                  :disabled="auditing && activeNodeId === node.id"
                  @click="handleApply(node.id, node.status)"
                >
                  应用
                </n-button>
              </div>

              <n-input
                v-if="getActionStatus(node.id, node.status) === 'archived'"
                :value="getReason(node.id)"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 4 }"
                placeholder="归档原因会发送给作者，并显示在归档节点上。"
                @update:value="setReason(node.id, $event)"
              />
            </div>
          </article>
        </div>
      </n-spin>
    </section>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 16px 48px;
}

.admin-hero {
  grid-template-columns: minmax(0, 1.8fr) minmax(220px, 0.9fr);
}

.admin-hero__metrics {
  display: grid;
  gap: 12px;
}

.admin-filters {
  display: grid;
  grid-template-columns: minmax(180px, 220px) minmax(0, 1fr) repeat(3, auto);
  gap: 12px;
  align-items: center;
}

.admin-filters__status {
  min-width: 0;
}

.audit-list {
  display: grid;
  gap: 16px;
}

.audit-card {
  display: grid;
  gap: 18px;
  padding: 18px;
}

.audit-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.audit-card__author {
  display: flex;
  align-items: center;
  gap: 12px;
}

.audit-card__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.02rem;
}

.audit-card__meta,
.audit-card__summary,
.audit-card__content,
.audit-card__hint {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.audit-card__badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.audit-card__section {
  display: grid;
  gap: 10px;
}

.audit-card__label {
  margin: 0;
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.audit-card__content {
  white-space: pre-wrap;
}

.audit-card__text-actions,
.audit-card__admin-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.audit-card__admin {
  gap: 12px;
}

.audit-card__admin-head {
  display: grid;
  gap: 6px;
}

.audit-card__admin-select {
  width: 180px;
}

@media (max-width: 900px) {
  .admin-hero {
    grid-template-columns: 1fr;
  }

  .admin-filters {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .admin-page {
    padding-inline: 12px;
  }

  .audit-card__header {
    flex-direction: column;
  }

  .audit-card__badges {
    justify-content: flex-start;
  }
}
</style>
