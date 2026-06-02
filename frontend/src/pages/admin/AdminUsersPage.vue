<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  NAvatar,
  NButton,
  NEmpty,
  NInput,
  NSelect,
  NSpin,
  NSwitch,
  NTag,
} from 'naive-ui'
import { useMessage } from 'naive-ui'

import type { UserRole } from '@/types/models'
import { useAdminStatsQuery, useAdminUpdateUserMutation, useAdminUsersQuery } from '@/features/admin/queries'

const message = useMessage()

const roleFilter = ref<UserRole | 'all'>('all')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const keyword = ref('')
const expandedUserId = ref<number | null>(null)
const activeUserId = ref<number | null>(null)

const draftState = ref<
  Record<
    number,
    {
      username: string
      bio: string
      avatar: string
      role: UserRole
      is_active: boolean
    }
  >
>({})

const queryParams = computed(() => ({
  role: roleFilter.value === 'all' ? undefined : roleFilter.value,
  is_active:
    statusFilter.value === 'all'
      ? undefined
      : statusFilter.value === 'active',
  keyword: keyword.value.trim() || undefined,
}))

const { data: users, isLoading, refetch } = useAdminUsersQuery(queryParams)
const { mutate: updateUser, isPending: updatingUser } = useAdminUpdateUserMutation()

const roleOptions: Array<{ label: string; value: UserRole }> = [
  { label: '管理员', value: 'admin' },
  { label: '作者', value: 'writer' },
  { label: '封禁', value: 'banned' },
]

// 全站真实用户总数来自 /admin/stats（按筛选命中数见 Phase B 的 X-Total-Count），不用截断列表 .length
const { data: adminStats } = useAdminStatsQuery()
const totalUsers = computed(() => adminStats.value?.users.total ?? users.value?.length ?? 0)

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

function getRoleType(role: UserRole) {
  switch (role) {
    case 'admin':
      return 'error'
    case 'writer':
      return 'success'
    case 'banned':
      return 'default'
  }
}

function ensureDraft(user: NonNullable<typeof users.value>[number]) {
  if (draftState.value[user.id]) return draftState.value[user.id]
  draftState.value = {
    ...draftState.value,
    [user.id]: {
      username: user.username,
      bio: user.bio || '',
      avatar: user.avatar || '',
      role: user.role,
      is_active: user.is_active,
    },
  }
  return draftState.value[user.id]
}

function toggleExpanded(user: NonNullable<typeof users.value>[number]) {
  if (expandedUserId.value === user.id) {
    expandedUserId.value = null
    return
  }
  ensureDraft(user)
  expandedUserId.value = user.id
}

function handleSaveUser(userId: number) {
  const draft = draftState.value[userId]
  if (!draft) return

  if (!draft.username.trim()) {
    message.error('用户名不能为空')
    return
  }

  activeUserId.value = userId
  updateUser(
    {
      userId,
      payload: {
        username: draft.username.trim(),
        bio: draft.bio.trim() || null,
        avatar: draft.avatar.trim() || null,
        role: draft.role,
        is_active: draft.is_active,
      },
    },
    {
      onSuccess: () => {
        message.success('用户资料已更新')
      },
      onError: () => {
        message.error('更新用户失败，请重试')
      },
      onSettled: () => {
        activeUserId.value = null
      },
    },
  )
}

function handleRefresh() {
  void refetch()
}
</script>

<template>
  <div class="ui-page-stack admin-page">
    <section class="ui-page-hero ui-shell-panel ui-shell-grid">
      <div class="ui-page-hero__grid admin-hero">
        <div>
          <p class="ui-shell-kicker">Admin / Users</p>
          <h1 class="ui-shell-title">用户管理</h1>
          <p class="ui-page-hero__lead">
            这里接入后端现有的用户列表与更新接口，管理员可以筛选角色、搜索账户，并直接修改角色和活跃状态。
          </p>
        </div>
        <div class="admin-hero__metrics">
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">用户总数</p>
            <p class="ui-metric-card__value">{{ totalUsers }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Filter</p>
          <h2 class="ui-shell-title">筛选用户</h2>
          <p class="ui-page-section__lead">按角色、活跃状态和关键词收束视图，再决定是否进入编辑。</p>
        </div>
        <n-button ghost @click="handleRefresh">刷新列表</n-button>
      </div>

      <div class="admin-filter-grid">
        <label class="admin-field">
          <span class="admin-field__label">角色</span>
          <n-select
            v-model:value="roleFilter"
            :options="[
              { label: '全部', value: 'all' },
              ...roleOptions,
            ]"
          />
        </label>

        <label class="admin-field">
          <span class="admin-field__label">状态</span>
          <n-select
            v-model:value="statusFilter"
            :options="[
              { label: '全部', value: 'all' },
              { label: '活跃', value: 'active' },
              { label: '停用', value: 'inactive' },
            ]"
          />
        </label>

        <label class="admin-field admin-field--wide">
          <span class="admin-field__label">关键词</span>
          <n-input
            v-model:value="keyword"
            placeholder="按用户名或邮箱搜索"
            clearable
          />
        </label>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Users</p>
          <h2 class="ui-shell-title">用户列表</h2>
          <p class="ui-page-section__lead">展开用户后，可直接修改角色、激活状态、用户名、简介和头像链接。</p>
        </div>
      </div>

      <n-spin :show="isLoading">
        <n-empty v-if="!users?.length" description="当前没有匹配的用户" />

        <div v-else class="admin-user-list">
          <article
            v-for="user in users"
            :key="user.id"
            class="admin-user-card ui-panel-section"
          >
            <div class="admin-user-card__header">
              <div class="admin-user-card__identity">
                <n-avatar :size="40" :src="user.avatar ?? undefined">
                  {{ user.username?.charAt(0).toUpperCase() }}
                </n-avatar>
                <div>
                  <h3 class="admin-user-card__title">{{ user.username }}</h3>
                  <p class="admin-user-card__meta">
                    {{ user.email }} · 注册于 {{ formatDateTime(user.created_at) }}
                  </p>
                </div>
              </div>

              <div class="admin-user-card__badges">
                <n-tag size="small" :type="getRoleType(user.role)">
                  {{ user.role }}
                </n-tag>
                <n-tag size="small" :type="user.is_active ? 'success' : 'default'">
                  {{ user.is_active ? 'active' : 'inactive' }}
                </n-tag>
              </div>
            </div>

            <div class="admin-user-card__summary">
              <span>简介：{{ user.bio || '暂无简介。' }}</span>
            </div>

            <div class="admin-user-card__actions">
              <n-button size="small" tertiary @click="toggleExpanded(user)">
                {{ expandedUserId === user.id ? '收起编辑' : '展开编辑' }}
              </n-button>
            </div>

            <div v-if="expandedUserId === user.id && draftState[user.id]" class="admin-user-editor">
              <label class="admin-field">
                <span class="admin-field__label">用户名</span>
                <n-input
                  :value="draftState[user.id]!.username"
                  @update:value="draftState[user.id]!.username = $event"
                />
              </label>

              <label class="admin-field">
                <span class="admin-field__label">角色</span>
                <n-select
                  :value="draftState[user.id]!.role"
                  :options="roleOptions"
                  @update:value="draftState[user.id]!.role = $event"
                />
              </label>

              <label class="admin-field admin-field--switch">
                <span class="admin-field__label">活跃状态</span>
                <div class="admin-switch-row">
                  <span class="admin-switch-row__hint">
                    {{ draftState[user.id]!.is_active ? '允许登录与使用' : '停用账户' }}
                  </span>
                  <n-switch
                    :value="draftState[user.id]!.is_active"
                    @update:value="draftState[user.id]!.is_active = $event"
                  />
                </div>
              </label>

              <label class="admin-field admin-field--wide">
                <span class="admin-field__label">简介</span>
                <n-input
                  :value="draftState[user.id]!.bio"
                  type="textarea"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                  @update:value="draftState[user.id]!.bio = $event"
                />
              </label>

              <label class="admin-field admin-field--wide">
                <span class="admin-field__label">头像链接</span>
                <n-input
                  :value="draftState[user.id]!.avatar"
                  @update:value="draftState[user.id]!.avatar = $event"
                />
              </label>

              <div class="admin-user-editor__actions">
                <n-button
                  type="primary"
                  :loading="updatingUser && activeUserId === user.id"
                  :disabled="updatingUser && activeUserId === user.id"
                  @click="handleSaveUser(user.id)"
                >
                  保存修改
                </n-button>
              </div>
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

.admin-filter-grid,
.admin-user-editor {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.admin-field {
  display: grid;
  gap: 8px;
}

.admin-field--wide {
  grid-column: 1 / -1;
}

.admin-field__label {
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.admin-field--switch {
  align-content: start;
}

.admin-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.03);
}

.admin-switch-row__hint {
  color: var(--text-secondary);
}

.admin-user-list {
  display: grid;
  gap: 16px;
}

.admin-user-card {
  display: grid;
  gap: 16px;
  padding: 18px;
}

.admin-user-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.admin-user-card__identity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-user-card__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.05rem;
}

.admin-user-card__meta,
.admin-user-card__summary {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.admin-user-card__badges,
.admin-user-card__actions,
.admin-user-editor__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 900px) {
  .admin-hero,
  .admin-filter-grid,
  .admin-user-editor {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .admin-page {
    padding-inline: 12px;
  }

  .admin-user-card__header {
    flex-direction: column;
  }
}
</style>
