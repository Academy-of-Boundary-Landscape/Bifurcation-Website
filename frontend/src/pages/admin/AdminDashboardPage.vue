<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NSpin } from 'naive-ui'

import { useAdminStatsQuery } from '@/features/admin/queries'

const router = useRouter()
const { data: stats, isLoading } = useAdminStatsQuery()

const statCards = computed(() => [
  {
    label: '待审核节点',
    value: stats.value?.nodes.pending ?? 0,
    hint: '需要管理员处理',
    actionLabel: '进入节点管理',
    routeName: 'admin-nodes',
  },
  {
    label: '近 7 日新增节点',
    value: stats.value?.nodes.new_7d ?? 0,
    hint: '观察内容活跃度',
    actionLabel: '查看故事册',
    routeName: 'admin-books',
  },
  {
    label: '已发布节点',
    value: stats.value?.nodes.published ?? 0,
    hint: '当前公开可见内容',
    actionLabel: '管理故事册',
    routeName: 'admin-books',
  },
  {
    label: '活跃用户',
    value: stats.value?.users.active ?? 0,
    hint: '当前可正常登录用户',
    actionLabel: '用户管理',
    routeName: 'admin-users',
  },
])

const operationalCards = computed(() => [
  {
    title: '审核工作台',
    summary: '集中处理待审核节点，查看正文、填写驳回原因并直接发布或归档。',
    routeName: 'admin-nodes',
  },
  {
    title: '故事册管理',
    summary: '创建新故事册，切换阶段，控制是否开放新节点创作。',
    routeName: 'admin-books',
  },
  {
    title: '用户管理',
    summary: '查看用户角色和活跃状态，维护后台权限与封禁状态。',
    routeName: 'admin-users',
  },
])

function goToAdminRoute(routeName: string) {
  void router.push({ name: routeName })
}
</script>

<template>
  <div class="ui-page-stack admin-page">
    <section class="ui-page-hero ui-shell-panel ui-shell-grid">
      <div class="ui-page-hero__grid admin-hero">
        <div>
          <p class="ui-shell-kicker">Admin / Console</p>
          <h1 class="ui-shell-title">管理员仪表盘</h1>
          <p class="ui-page-hero__lead">
            这里不是一组花哨卡片，而是后台主操作入口。管理员应该能从这里快速判断积压、活跃度和最需要处理的工作。
          </p>
        </div>
        <div class="admin-hero__summary ui-panel-section">
          <p class="admin-hero__summary-label">当前状态</p>
          <p class="admin-hero__summary-value">
            {{ stats?.nodes.pending ?? 0 }} 个待审核节点
          </p>
          <p class="admin-hero__summary-note">
            {{ stats?.users.new_7d ?? 0 }} 位新用户 / {{ stats?.nodes.new_7d ?? 0 }} 个新节点（近 7 日）
          </p>
        </div>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Metrics</p>
          <h2 class="ui-shell-title">运营概览</h2>
          <p class="ui-page-section__lead">这些统计来自后端真实 `/admin/stats`，不再展示伪造的最近活动。</p>
        </div>
      </div>

      <n-spin :show="isLoading">
        <div class="admin-metric-grid">
          <n-card
            v-for="card in statCards"
            :key="card.label"
            class="ui-panel-section admin-metric-card"
            :bordered="false"
          >
            <p class="admin-metric-card__label">{{ card.label }}</p>
            <p class="admin-metric-card__value">{{ card.value }}</p>
            <p class="admin-metric-card__hint">{{ card.hint }}</p>
            <n-button
              size="small"
              type="primary"
              @click="goToAdminRoute(card.routeName)"
            >
              {{ card.actionLabel }}
            </n-button>
          </n-card>
        </div>
      </n-spin>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Operations</p>
          <h2 class="ui-shell-title">核心操作入口</h2>
          <p class="ui-page-section__lead">后台优先服务三类任务：审核内容、维护故事册、管理用户。</p>
        </div>
      </div>

      <div class="admin-operational-grid">
        <article
          v-for="card in operationalCards"
          :key="card.title"
          class="admin-operational-card ui-panel-section"
        >
          <h3 class="admin-operational-card__title">{{ card.title }}</h3>
          <p class="admin-operational-card__summary">{{ card.summary }}</p>
          <n-button
            size="small"
            type="primary"
            @click="goToAdminRoute(card.routeName)"
          >
            打开页面
          </n-button>
        </article>
      </div>
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
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.9fr);
  align-items: start;
}

.admin-hero__summary {
  display: grid;
  gap: 10px;
  padding: 18px;
}

.admin-hero__summary-label {
  margin: 0;
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.admin-hero__summary-value {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.75rem;
}

.admin-hero__summary-note {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.admin-metric-grid,
.admin-operational-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.admin-metric-card,
.admin-operational-card {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.admin-metric-card__label {
  margin: 0;
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.admin-metric-card__value {
  margin: 0;
  font-family: var(--font-display);
  font-size: 2rem;
  line-height: 1;
}

.admin-metric-card__hint,
.admin-operational-card__summary {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.admin-operational-card__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.05rem;
}

@media (max-width: 900px) {
  .admin-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .admin-page {
    padding-inline: 12px;
  }
}
</style>
