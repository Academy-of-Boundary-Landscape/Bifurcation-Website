<script setup lang="ts">
import { computed, ref } from 'vue'
import { NButton, NInput } from 'naive-ui'
import { useRouter } from 'vue-router'
import DiscoveryRail from '@/components/discovery/DiscoveryRail.vue'
import DiscoveryNodeCard from '@/components/discovery/DiscoveryNodeCard.vue'
import { useDiscoverySearchQuery, useFeaturedNodesQuery, useLatestFeedQuery, useTrendingNodesQuery } from '@/features/discovery/queries'
import type { DiscoveryRailItem } from '@/types/discovery'

const router = useRouter()

const principles = [
  {
    code: '01',
    title: '树状叙事',
    description: '每个节点都不是终点，而是进入另一条世界线的精确入口。',
  },
  {
    code: '02',
    title: '共同创作',
    description: '读者可以顺着任意关键节点续写，让故事在分歧点继续分裂。',
  },
  {
    code: '03',
    title: '审核发布',
    description: '所有新增内容先进入待审流程，前台只展示已经发布的世界线。',
  },
]

const workflow = [
  {
    code: 'A1',
    title: '进入故事册',
    description: '先查看已有世界线的结构，再决定从哪条路径开始阅读。',
  },
  {
    code: 'A2',
    title: '锁定节点',
    description: '在树上定位分歧点，阅读节点正文和当前分支的上下文。',
  },
  {
    code: 'A3',
    title: '接入续写',
    description: '围绕当前节点创建新分支，把你的版本接入主系统。',
  },
  {
    code: 'A4',
    title: '等待审核',
    description: '管理员审查通过后，新节点会正式出现在故事树与分支阅读里。',
  },
]

const searchKeyword = ref('')
const normalizedSearchKeyword = computed(() => searchKeyword.value.trim())

const { data: featuredNodes, isLoading: featuredLoading, error: featuredError } = useFeaturedNodesQuery({ limit: 4 })
const { data: latestFeed, isLoading: latestFeedLoading, error: latestFeedError } = useLatestFeedQuery({ limit: 4 })
const { data: trendingNodes, isLoading: trendingLoading, error: trendingError } = useTrendingNodesQuery({ days: 7, limit: 4 })
const {
  data: searchResults,
  isLoading: searchLoading,
  error: searchError,
} = useDiscoverySearchQuery(normalizedSearchKeyword, { limit: 6 })

function formatDate(value: string | null | undefined) {
  if (!value) return '未标记时间'
  return new Date(value).toLocaleDateString('zh-CN')
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    published: '已发布',
    pending: '待审核',
    archived: '已归档',
  }

  return labels[status] ?? status
}

function toDiscoveryItem(
  node: {
    id: number
    book_id: number
    title: string | null
    summary: string | null
    author: { username: string }
    status: string
    likes_count: number
    comments_count: number
    children_count: number
    published_at: string | null
    created_at: string
  },
  options?: {
    badge?: string
    badgeTone?: 'default' | 'strong'
    metrics?: DiscoveryRailItem['metrics']
    hint?: string
    actionLabel?: string
    meta?: string[]
  },
): DiscoveryRailItem {
  return {
    id: node.id,
    title: node.title || '未命名节点',
    summary: node.summary || '该节点暂未提供摘要，请进入正文查看完整内容。',
    badge: options?.badge ?? getStatusLabel(node.status),
    badgeTone: options?.badgeTone,
    meta: options?.meta ?? [`Author ${node.author.username}`, formatDate(node.published_at || node.created_at)],
    metrics: options?.metrics,
    hint: options?.hint ?? `Book ${node.book_id} · 节点 ${node.id}`,
    action: {
      label: options?.actionLabel ?? '查看正文',
      to: `/story/node/${node.id}`,
    },
  }
}

const latestFeedItems = computed(() =>
  (latestFeed.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      actionLabel: '查看正文',
    }),
  ),
)

const featuredItems = computed(() =>
  (featuredNodes.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: node.feature_rank ? `Rank ${node.feature_rank}` : 'Featured',
      badgeTone: 'strong',
      metrics: [
        { label: 'Likes', value: String(node.likes_count) },
        { label: 'Children', value: String(node.children_count) },
      ],
      hint: `Book ${node.book_id} · 精选节点`,
      actionLabel: '进入节点',
      meta: [`Author ${node.author.username}`, formatDate(node.published_at || node.created_at)],
    }),
  ),
)

const trendingItems = computed(() =>
  (trendingNodes.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: `Likes ${node.likes_count}`,
      badgeTone: 'strong',
      metrics: [
        { label: 'Children', value: String(node.children_count) },
        { label: 'Comments', value: String(node.comments_count) },
      ],
      hint: `Author ${node.author.username}`,
      actionLabel: '进入节点',
      meta: [formatDate(node.published_at || node.created_at)],
    }),
  ),
)

const searchItems = computed(() =>
  (searchResults.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: `Book ${node.book_id}`,
      hint: formatDate(node.published_at || node.created_at),
      actionLabel: '打开节点',
      meta: [`Author ${node.author.username}`, `Likes ${node.likes_count}`],
    }),
  ),
)

function goTo(path: string) {
  void router.push(path)
}
</script>

<template>
  <div class="ui-page-stack">
    <section class="ui-page-hero ui-shell-panel ui-shell-panel--raised ui-shell-grid home-hero">
      <div class="ui-page-hero__grid">
        <div class="home-hero__copy">
          <p class="ui-shell-kicker">Narrative Observation System</p>
          <h1 class="ui-shell-title home-hero__title">
            分岔视界
          </h1>
          <p class="home-hero__subline">
            Bifurcation Horizon
          </p>
          <p class="ui-page-hero__lead">
            这是一个树状结构的小说续写平台。你可以先观察整棵故事树，再进入单个节点阅读、沿当前路径继续推进，或在关键分歧处开辟新的世界线。
          </p>
          <div class="ui-page-hero__actions">
            <n-button type="primary" size="large" @click="goTo('/books')">
              进入故事册
            </n-button>
            <n-button quaternary size="large" @click="goTo('/register')">
              连接 SSO 并创作
            </n-button>
          </div>
        </div>

        <div class="home-hero__metrics">
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Core Mode</p>
            <p class="ui-metric-card__value">Tree</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Reading Model</p>
            <p class="ui-metric-card__value">Node / Lineage</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Creation Gate</p>
            <p class="ui-metric-card__value">Review First</p>
          </div>
        </div>
      </div>
    </section>

    <DiscoveryRail
      kicker="Featured Selection"
      title="精选节点"
      description="这一栏直接消费后端的精选接口。当前规则很克制，只基于管理员标记的 `is_featured + feature_rank`，先把运营可控的推荐位跑通。"
      :items="featuredItems"
      :loading="featuredLoading"
      :error="featuredError as Error | null"
      empty-text="当前还没有设置精选节点。"
      action-label="查看全部故事册"
      action-to="/books"
    />

    <DiscoveryRail
      kicker="Live Feed"
      title="最新更新"
      description="这里直接接入后端现有的最新动态接口，让首页不仅是说明书，也能显示平台此刻正在发生的叙事活动。"
      :items="latestFeedItems"
      :loading="latestFeedLoading"
      :error="latestFeedError as Error | null"
      empty-text="还没有已发布的新节点。"
      action-label="查看全部故事册"
      action-to="/books"
    />

    <DiscoveryRail
      kicker="Trending"
      title="热门节点"
      description="这一块直接使用后端现有的热门接口。当前是节点级热度，不是整条世界线榜，但已经足够给首页提供一个从哪里开始读的入口。"
      :items="trendingItems"
      :loading="trendingLoading"
      :error="trendingError as Error | null"
      empty-text="还没有形成热门节点。"
    />

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Search</p>
          <h2 class="ui-shell-title">节点搜索</h2>
          <p class="ui-page-section__lead">
            后端已经有基于标题和正文的搜索接口。这里先把它收成一个克制的首页搜索区，而不是另起一个复杂的发现页面。
          </p>
        </div>
      </div>

      <div class="home-search">
        <n-input
          v-model:value="searchKeyword"
          clearable
          placeholder="输入节点标题或正文关键词"
          class="home-search__input"
        />
      </div>

      <div v-if="normalizedSearchKeyword.length === 0" class="ui-status-note">
        输入关键词后，会直接显示当前已发布节点的搜索结果。
      </div>
      <div v-else-if="searchLoading" class="home-feed-state">
        <n-spin size="large" />
      </div>
      <div v-else-if="searchError" class="ui-status-note ui-status-note--danger">
        搜索失败：{{ (searchError as Error).message }}
      </div>
      <div v-else-if="!searchResults?.length" class="ui-status-note">
        没有匹配的已发布节点。
      </div>
      <div v-else class="ui-card-list ui-card-list--books">
        <DiscoveryNodeCard
          v-for="item in searchItems"
          :key="`search-${item.id}`"
          :item="item"
        />
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">System Traits</p>
          <h2 class="ui-shell-title">平台结构</h2>
          <p class="ui-page-section__lead">
            首页不负责讲故事细节，只负责说明这套系统怎样让阅读、导航与共同创作在同一棵树里发生。
          </p>
        </div>
      </div>

      <div class="ui-card-list ui-card-list--three">
        <article
          v-for="item in principles"
          :key="item.code"
          class="ui-archive-card ui-panel-section"
        >
          <div class="ui-archive-card__meta">
            <span>{{ item.code }}</span>
          </div>
          <div>
            <h3 class="ui-archive-card__title">{{ item.title }}</h3>
            <p class="ui-archive-card__lead">{{ item.description }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Participation Flow</p>
          <h2 class="ui-shell-title">参与流程</h2>
          <p class="ui-page-section__lead">
            读者和创作者并不是两个完全割裂的角色。这个平台的理想体验，是用户先理解世界线，再在某个节点自然地产生续写冲动。
          </p>
        </div>
      </div>

      <div class="ui-card-list ui-card-list--books">
        <article
          v-for="step in workflow"
          :key="step.code"
          class="ui-archive-card ui-panel-section"
        >
          <div class="ui-archive-card__meta">
            <span>{{ step.code }}</span>
          </div>
          <div>
            <h3 class="ui-archive-card__title">{{ step.title }}</h3>
            <p class="ui-archive-card__lead">{{ step.description }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel home-entry">
      <div class="ui-page-section__header home-entry__header">
        <div>
          <p class="ui-shell-kicker">Entry Point</p>
          <h2 class="ui-shell-title">开始观测</h2>
          <p class="ui-page-section__lead">
            下一步应该进入故事册列表，而不是停留在首页。故事树、节点阅读和分支创作的完整体验，都从书页开始。
          </p>
        </div>
        <n-button type="primary" size="large" @click="goTo('/books')">
          打开故事册列表
        </n-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-hero__title {
  font-size: clamp(2.8rem, 6vw, 5rem);
}

.home-hero__subline {
  margin: 12px 0 0;
  color: var(--text-faint);
  font-family: var(--font-mono);
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.home-hero__copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.home-hero__metrics {
  display: grid;
  gap: 14px;
}

.home-entry__header {
  align-items: center;
}

.home-search {
  margin-bottom: 18px;
}

.home-search__input {
  max-width: 520px;
}

@media (min-width: 980px) {
  .home-hero__metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
const router = useRouter()
