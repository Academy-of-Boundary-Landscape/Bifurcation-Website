<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpin, NTag } from 'naive-ui'
import { useMessage } from 'naive-ui'

import type { Notification } from '@/types/models'
import {
  useMarkAllNotificationsAsReadMutation,
  useMarkNotificationAsReadMutation,
  useInfiniteNotificationsQuery,
  useUnreadCountQuery,
} from '@/features/interaction/queries'

type NotificationFilter = 'all' | Notification['type']

const message = useMessage()
const router = useRouter()
const filterType = ref<NotificationFilter>('all')
const markingNotificationId = ref<number | null>(null)

const {
  data: notificationPages,
  isLoading,
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage,
} = useInfiniteNotificationsQuery()
const { data: unreadCount } = useUnreadCountQuery()
const { mutate: markAsRead, isPending: marking } = useMarkNotificationAsReadMutation()
const { mutate: markAllAsRead, isPending: markingAll } = useMarkAllNotificationsAsReadMutation()

const filterOptions: Array<{ value: NotificationFilter; label: string }> = [
  { value: 'all', label: '全部' },
  { value: 'branched', label: '新分支' },
  { value: 'liked', label: '点赞' },
  { value: 'commented', label: '评论' },
  { value: 'approved', label: '审核通过' },
  { value: 'rejected', label: '审核驳回' },
]

const allNotifications = computed(() => notificationPages.value?.pages.flatMap((p) => p.items) ?? [])

const filteredNotifications = computed(() => {
  if (filterType.value === 'all') return allNotifications.value
  return allNotifications.value.filter((n) => n.type === filterType.value)
})

const unreadCountValue = computed(() => unreadCount.value?.unread_count ?? 0)
// 真实通知总数来自 X-Total-Count（首页返回的 total），不随无限滚动加载量变化
const totalCount = computed(() => notificationPages.value?.pages[0]?.total ?? allNotifications.value.length)

function setFilter(type: NotificationFilter) {
  filterType.value = type
}

function formatDateTime(value: string) {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '时间未知'

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed)
}

function getNotificationTitle(notification: Notification) {
  const actor = notification.sender?.username || '系统'
  switch (notification.type) {
    case 'branched':
      return `${actor} 创建了新分支`
    case 'liked':
      return `${actor} 点赞了您的节点`
    case 'commented':
      return `${actor} 评论了您的节点`
    case 'approved':
      return '您的投稿已通过审核'
    case 'rejected':
      return '您的投稿未通过审核'
    default:
      return notification.message || '系统通知'
  }
}

function getNotificationBody(notification: Notification) {
  if (notification.type === 'rejected' && notification.message) {
    return `审核未通过：${notification.message}`
  }
  if (notification.message) return notification.message

  switch (notification.type) {
    case 'branched':
      return '有用户沿着您的节点继续延展了新的世界线。'
    case 'liked':
      return '您的节点获得了一次新的正向反馈。'
    case 'commented':
      return '有用户对您的节点留下了新的评论。'
    case 'approved':
      return '节点已进入公开可见状态，其他读者现在可以在前台看到它。'
    case 'rejected':
      return '节点当前未进入前台展示状态，请检查审核反馈。'
    default:
      return '请进入相关节点查看详情。'
  }
}

function getNotificationBadge(notification: Notification) {
  switch (notification.type) {
    case 'branched':
      return { label: 'BRANCH', type: 'success' as const }
    case 'liked':
      return { label: 'LIKE', type: 'warning' as const }
    case 'commented':
      return { label: 'COMMENT', type: 'info' as const }
    case 'approved':
      return { label: 'APPROVED', type: 'success' as const }
    case 'rejected':
      return { label: 'REJECTED', type: 'error' as const }
    default:
      return { label: 'NOTICE', type: 'default' as const }
  }
}

function handleMarkAsRead(notificationId: number) {
  markingNotificationId.value = notificationId
  markAsRead(
    { notificationId },
    {
      onSuccess: () => {
        message.success('通知状态已更新')
        markingNotificationId.value = null
      },
      onError: () => {
        message.error('标记失败，请重试')
        markingNotificationId.value = null
      },
    },
  )
}

function handleMarkAllAsRead() {
  markAllAsRead(undefined, {
    onSuccess: () => {
      message.success('所有通知已标记为已读')
    },
    onError: () => {
      message.error('标记失败，请重试')
    },
  })
}

function goToBooks() {
  void router.push({ name: 'books' })
}

function openNotificationNode(nodeId: number) {
  void router.push({ name: 'story-node', params: { nodeId } })
}
</script>

<template>
  <div class="ui-page-stack">
    <section class="ui-page-hero ui-shell-panel ui-shell-grid notification-hero">
      <div class="ui-page-hero__grid notification-hero__grid">
        <div>
          <p class="ui-shell-kicker">Signal Inbox</p>
          <h1 class="ui-shell-title notification-hero__title">通知中心</h1>
          <p class="ui-page-hero__lead">
            这里集中显示分支延伸、点赞、评论和审核结果。通知页不该像一串零碎消息，而应该像一块叙事状态面板。
          </p>
        </div>

        <div class="notification-hero__metrics">
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Total</p>
            <p class="ui-metric-card__value">{{ totalCount }}</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Unread</p>
            <p class="ui-metric-card__value">{{ unreadCountValue }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Filter</p>
          <h2 class="ui-shell-title">筛选通知类型</h2>
          <p class="ui-page-section__lead">
            先按信号类型收束视图，再决定要不要进入对应节点。
          </p>
        </div>

        <n-button
          type="primary"
          :disabled="markingAll || unreadCountValue === 0"
          :loading="markingAll"
          @click="handleMarkAllAsRead"
        >
          全部标记为已读
        </n-button>
      </div>

      <div class="ui-filter-row">
        <button
          v-for="option in filterOptions"
          :key="option.value"
          type="button"
          class="notification-filter"
          :class="{ 'notification-filter--active': filterType === option.value }"
          @click="setFilter(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Feed</p>
          <h2 class="ui-shell-title">通知流</h2>
          <p class="ui-page-section__lead">
            当前筛选结果 {{ filteredNotifications.length }} 条。
          </p>
        </div>
      </div>

      <n-spin :show="isLoading">
        <div v-if="!filteredNotifications.length" class="notification-empty ui-panel-section">
          <p class="notification-empty__icon">SIGNAL / 00</p>
          <h3 class="ui-shell-title">当前没有可显示的通知</h3>
          <p class="ui-page-section__lead">
            你可以先去故事册里继续阅读或创作，新的互动和审核结果会回到这里。
          </p>
          <n-button type="primary" @click="goToBooks">
            返回故事册
          </n-button>
        </div>

        <div v-else class="notification-list">
          <article
            v-for="notification in filteredNotifications"
            :key="notification.id"
            class="notification-card ui-panel-section"
            :class="{ 'notification-card--unread': !notification.is_read }"
          >
            <div class="notification-card__head">
              <div class="notification-card__meta">
                <n-tag size="small" :type="getNotificationBadge(notification).type">
                  {{ getNotificationBadge(notification).label }}
                </n-tag>
                <span class="notification-card__time">{{ formatDateTime(notification.created_at) }}</span>
                <span v-if="!notification.is_read" class="notification-card__state">UNREAD</span>
              </div>

              <div class="notification-card__actions">
                <n-button
                  v-if="!notification.is_read"
                  size="small"
                  tertiary
                  :loading="marking && markingNotificationId === notification.id"
                  :disabled="marking && markingNotificationId === notification.id"
                  @click="handleMarkAsRead(notification.id)"
                >
                  标记已读
                </n-button>
                <n-button
                  v-if="notification.node_id"
                  type="primary"
                  size="small"
                  @click="openNotificationNode(notification.node_id!)"
                >
                  查看节点
                </n-button>
              </div>
            </div>

            <div class="notification-card__body">
              <h3 class="notification-card__title">
                {{ getNotificationTitle(notification) }}
              </h3>
              <p class="notification-card__summary">
                {{ getNotificationBody(notification) }}
              </p>
            </div>
          </article>

          <div v-if="hasNextPage" class="notification-load-more">
            <n-button
              :loading="isFetchingNextPage"
              :disabled="isFetchingNextPage"
              @click="fetchNextPage()"
            >
              加载更多
            </n-button>
          </div>
          <p v-else-if="allNotifications.length > 0" class="notification-end-hint">
            已显示全部通知
          </p>
        </div>
      </n-spin>
    </section>
  </div>
</template>

<style scoped>
.notification-hero__grid {
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
  align-items: start;
}

.notification-hero__title {
  font-size: clamp(2.2rem, 5vw, 3.4rem);
}

.notification-hero__metrics {
  display: grid;
  gap: 14px;
}

.notification-filter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    color var(--transition-fast),
    background var(--transition-fast),
    box-shadow var(--transition-fast);
}

.notification-filter:hover {
  border-color: var(--line-strong);
  color: var(--text-primary);
}

.notification-filter--active {
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  box-shadow: var(--glow-focus);
}

.notification-list {
  display: grid;
  gap: 16px;
}

.notification-card {
  display: grid;
  gap: 16px;
  padding: 20px;
}

.notification-card--unread {
  border-color: var(--line-strong);
  box-shadow: var(--glow-focus);
}

.notification-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.notification-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.notification-card__time,
.notification-card__state {
  color: var(--text-faint);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.notification-card__state {
  color: var(--accent-bright);
}

.notification-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.notification-card__body {
  display: grid;
  gap: 10px;
}

.notification-card__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.1rem;
  letter-spacing: 0.03em;
}

.notification-card__summary {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.notification-load-more {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.notification-end-hint {
  margin: 0;
  text-align: center;
  color: var(--text-faint);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 8px 0;
}

.notification-empty {
  display: grid;
  justify-items: start;
  gap: 14px;
  padding: 28px;
}

.notification-empty__icon {
  margin: 0;
  color: var(--text-faint);
  font-family: var(--font-mono);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

@media (max-width: 900px) {
  .notification-hero__grid {
    grid-template-columns: 1fr;
  }

  .notification-card__head {
    flex-direction: column;
  }

  .notification-card__actions {
    justify-content: flex-start;
  }
}
</style>
