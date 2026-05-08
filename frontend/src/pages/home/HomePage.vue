<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { NButton, NInput, NSpin } from 'naive-ui'
import { useRouter } from 'vue-router'
import DiscoveryRail from '@/components/discovery/DiscoveryRail.vue'
import DiscoveryNodeCard from '@/components/discovery/DiscoveryNodeCard.vue'
import {
  useDiscoverySearchQuery,
  useFeaturedNodesQuery,
  useLatestFeedQuery,
  useTrendingNodesQuery,
} from '@/features/discovery/queries'
import { buildStoryWriteRoute } from '@/features/story/navigation'
import { useAuthStore } from '@/stores/auth'
import type { DiscoveryRailItem } from '@/types/discovery'

const router = useRouter()
const authStore = useAuthStore()

/* ============ 草稿恢复（方案 B）============
 * StoryWritePage 把每篇草稿存在 localStorage：
 *   key = `bifurcation_story_node_draft:{bookId}:parent:{parentId|root}`
 *   value = { version, savedAt, data: { book_id, parent_id, title, content, ... } }
 * 这里扫一下，挑最新的一条在 hero 里浮出来。
 */
interface DraftPreview {
  bookId: number
  parentId: number | null
  title: string
  savedAt: string
  preview: string
}

const latestDraft = ref<DraftPreview | null>(null)

function scanLatestDraft(): DraftPreview | null {
  if (typeof window === 'undefined') return null
  const PREFIX = 'bifurcation_story_node_draft:'
  let best: DraftPreview | null = null
  for (let i = 0; i < window.localStorage.length; i += 1) {
    const key = window.localStorage.key(i)
    if (!key || !key.startsWith(PREFIX)) continue
    try {
      const raw = window.localStorage.getItem(key)
      if (!raw) continue
      const parsed = JSON.parse(raw) as {
        savedAt?: string
        data?: { book_id?: number; parent_id?: number | null; title?: string; content?: string }
      }
      const data = parsed?.data
      const savedAt = parsed?.savedAt
      if (!data?.book_id || !savedAt) continue
      // 内容完全空的草稿不展示
      const hasContent = (data.title?.trim() || data.content?.trim())
      if (!hasContent) continue
      const candidate: DraftPreview = {
        bookId: Number(data.book_id),
        parentId: data.parent_id ?? null,
        title: data.title?.trim() || '未命名草稿',
        savedAt,
        preview: (data.content ?? '').replace(/\s+/g, ' ').trim().slice(0, 80),
      }
      if (!best || new Date(candidate.savedAt) > new Date(best.savedAt)) {
        best = candidate
      }
    } catch {
      // 损坏的草稿忽略
    }
  }
  return best
}

function formatDraftTime(value: string) {
  const d = new Date(value)
  const now = new Date()
  const diffMin = Math.floor((now.getTime() - d.getTime()) / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

function resumeDraft() {
  if (!latestDraft.value) return
  void router.push(buildStoryWriteRoute(latestDraft.value.bookId, latestDraft.value.parentId))
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    latestDraft.value = scanLatestDraft()
  }
})

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

// Hero metadata bar — clinical / dossier feel
const today = new Date()
const todayStamp = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, '0')}.${String(today.getDate()).padStart(2, '0')}`

// Aggregate counts from cached queries (best-effort — undefined falls through to "—")
const totalLatest = computed(() => latestFeed.value?.length ?? null)
const totalFeatured = computed(() => featuredNodes.value?.length ?? null)
const totalTrending = computed(() => trendingNodes.value?.length ?? null)

function fmtCount(n: number | null) {
  if (n == null) return '—'
  return String(n).padStart(2, '0')
}

function formatDate(value: string | null | undefined) {
  if (!value) return '——'
  const d = new Date(value)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    published: 'PUB',
    pending: 'PEND',
    archived: 'ARCH',
  }
  return labels[status] ?? status.toUpperCase()
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
  const item: DiscoveryRailItem = {
    id: node.id,
    title: node.title || '未命名节点',
    summary: node.summary || '该节点暂未提供摘要。',
    badge: options?.badge ?? getStatusLabel(node.status),
    badgeTone: options?.badgeTone,
    meta: options?.meta ?? [`@${node.author.username}`, formatDate(node.published_at || node.created_at)],
    metrics: options?.metrics,
    hint: options?.hint ?? `BOOK-${node.book_id} · NODE-${node.id}`,
    action: {
      label: options?.actionLabel ?? '阅读节点',
      to: `/story/node/${node.id}`,
    },
  }
  // 方案 A：登录用户能直接从首页卡片跳到写作页（仅对已发布节点）
  if (authStore.isAuthenticated && node.status === 'published') {
    item.secondaryAction = {
      label: '续写 →',
      to: buildStoryWriteRoute(node.book_id, node.id),
    }
  }
  return item
}

const featuredItems = computed(() =>
  (featuredNodes.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: node.feature_rank ? `FX-${String(node.feature_rank).padStart(2, '0')}` : 'FX',
      badgeTone: 'strong',
      metrics: [
        { label: 'LIKES', value: String(node.likes_count) },
        { label: 'CHILDREN', value: String(node.children_count) },
      ],
      hint: `BOOK-${node.book_id}`,
      actionLabel: '调阅节点',
      meta: [`@${node.author.username}`, formatDate(node.published_at || node.created_at)],
    }),
  ),
)

const latestFeedItems = computed(() =>
  (latestFeed.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      actionLabel: '调阅节点',
    }),
  ),
)

const trendingItems = computed(() =>
  (trendingNodes.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: `T+${node.likes_count}`,
      badgeTone: 'strong',
      metrics: [
        { label: 'CHILDREN', value: String(node.children_count) },
        { label: 'COMMENTS', value: String(node.comments_count) },
      ],
      hint: `@${node.author.username}`,
      actionLabel: '调阅节点',
      meta: [formatDate(node.published_at || node.created_at)],
    }),
  ),
)

const searchItems = computed(() =>
  (searchResults.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: `BOOK-${node.book_id}`,
      hint: formatDate(node.published_at || node.created_at),
      actionLabel: '调阅节点',
      meta: [`@${node.author.username}`, `LIKES ${node.likes_count}`],
    }),
  ),
)

function goTo(path: string) {
  void router.push(path)
}
</script>

<template>
  <div class="home">
    <!-- ============ HERO / DOSSIER ============ -->
    <section class="hero">
      <!-- top metadata strip -->
      <div class="hero__strip">
        <span class="hero__strip-cell">§00 / BIFURCATION</span>
        <span class="hero__strip-cell">OBS-PUBLIC</span>
        <span class="hero__strip-cell hero__strip-cell--right">{{ todayStamp }}</span>
      </div>

      <!-- 草稿待续 banner（仅在登录态 + 有非空草稿时显示）-->
      <div v-if="latestDraft" class="hero__draft" role="region" aria-label="草稿待续">
        <div class="hero__draft-meta">
          <span class="hero__draft-tag">DRAFT · 草稿待续</span>
          <span class="hero__draft-locator">
            BOOK-{{ latestDraft.bookId }}<template v-if="latestDraft.parentId !== null"> · 接续 NODE-{{ latestDraft.parentId }}</template><template v-else> · 主干起点</template>
          </span>
          <span class="hero__draft-time">{{ formatDraftTime(latestDraft.savedAt) }}</span>
        </div>
        <p class="hero__draft-preview">
          <span class="hero__draft-title">{{ latestDraft.title }}</span>
          <span v-if="latestDraft.preview" class="hero__draft-snippet">— {{ latestDraft.preview }}{{ latestDraft.preview.length >= 80 ? '…' : '' }}</span>
        </p>
        <button type="button" class="hero__draft-cta" @click="resumeDraft">
          继续未完成的写作
          <span aria-hidden="true">→</span>
        </button>
      </div>

      <div class="hero__inner">
        <div class="hero__copy">
          <p class="hero__kicker">分岔档案 · 观测条目 §00.01</p>

          <h1 class="hero__title">
            <span class="hero__title-glyph hero__title-glyph--1">分</span><span class="hero__title-glyph hero__title-glyph--2">岔</span>
          </h1>

          <p class="hero__sub">Bifurcation / a tree-shaped narrative archive</p>

          <p class="hero__lead">
            一座以树状结构生长的协同小说档案。每一段叙述都被记录为一个节点；每一处分歧都被允许同时存在。
            读者既可以沿原路径推进，也可以在任何节点处建立新的分支。
          </p>

          <div class="hero__actions">
            <n-button class="hero__cta hero__cta--primary" size="large" @click="goTo('/books')">
              进入档案
              <span class="hero__cta-arrow" aria-hidden="true">→</span>
            </n-button>
            <button v-if="!authStore.isAuthenticated" class="hero__cta-link" type="button" @click="goTo('/login')">
              登记观测者身份
            </button>
            <button v-else class="hero__cta-link" type="button" @click="goTo('/notifications')">
              查看新分支记录
            </button>
          </div>

          <!-- 显示当前 hero 上能调阅到的样本数（不是站点真实总数）。
               想要真实总数需要后端开 count 接口；当前是 query.length，受 limit 截断。 -->
          <dl class="hero__telemetry">
            <div class="hero__telem">
              <dt>SHOWN · 编辑标记</dt>
              <dd>{{ fmtCount(totalFeatured) }}</dd>
            </div>
            <div class="hero__telem">
              <dt>SHOWN · 近期入档</dt>
              <dd>{{ fmtCount(totalLatest) }}</dd>
            </div>
            <div class="hero__telem">
              <dt>SHOWN · 高度关注</dt>
              <dd>{{ fmtCount(totalTrending) }}</dd>
            </div>
          </dl>
        </div>

        <!-- Schematic dendrogram on the right — orthogonal lines, no glow -->
        <figure class="hero__schematic" aria-hidden="true">
          <figcaption class="hero__schematic-caption">FIG. 1 — TREE TOPOLOGY (SCHEMATIC)</figcaption>
          <svg viewBox="0 0 400 460" preserveAspectRatio="xMidYMid meet" class="schematic">
            <!-- horizontal & vertical hairlines for measurement feel -->
            <g class="schematic__grid">
              <line x1="40" y1="50" x2="40" y2="430" />
              <line x1="40" y1="430" x2="380" y2="430" />
            </g>

            <!-- trunk -->
            <line x1="220" y1="430" x2="220" y2="320" class="schematic__line schematic__line--trunk" />

            <!-- level 1: trunk → 3 primary branches -->
            <line x1="220" y1="320" x2="120" y2="320" class="schematic__line" />
            <line x1="220" y1="320" x2="320" y2="320" class="schematic__line" />
            <line x1="120" y1="320" x2="120" y2="230" class="schematic__line" />
            <line x1="220" y1="320" x2="220" y2="230" class="schematic__line" />
            <line x1="320" y1="320" x2="320" y2="230" class="schematic__line" />

            <!-- level 2: each primary → 2 secondaries -->
            <line x1="120" y1="230" x2="80" y2="230" class="schematic__line" />
            <line x1="120" y1="230" x2="160" y2="230" class="schematic__line" />
            <line x1="80" y1="230" x2="80" y2="150" class="schematic__line" />
            <line x1="160" y1="230" x2="160" y2="150" class="schematic__line" />

            <line x1="220" y1="230" x2="190" y2="230" class="schematic__line" />
            <line x1="220" y1="230" x2="250" y2="230" class="schematic__line" />
            <line x1="190" y1="230" x2="190" y2="150" class="schematic__line" />
            <line x1="250" y1="230" x2="250" y2="150" class="schematic__line" />

            <line x1="320" y1="230" x2="290" y2="230" class="schematic__line" />
            <line x1="320" y1="230" x2="360" y2="230" class="schematic__line" />
            <line x1="290" y1="230" x2="290" y2="150" class="schematic__line" />
            <line x1="360" y1="230" x2="360" y2="150" class="schematic__line" />

            <!-- terminal tick marks -->
            <line x1="74" y1="150" x2="86" y2="150" class="schematic__tick" />
            <line x1="154" y1="150" x2="166" y2="150" class="schematic__tick" />
            <line x1="184" y1="150" x2="196" y2="150" class="schematic__tick" />
            <line x1="244" y1="150" x2="256" y2="150" class="schematic__tick" />
            <line x1="284" y1="150" x2="296" y2="150" class="schematic__tick" />
            <line x1="354" y1="150" x2="366" y2="150" class="schematic__tick" />

            <!-- node labels (mono) -->
            <text x="220" y="445" class="schematic__label">root</text>
            <text x="120" y="345" class="schematic__label schematic__label--small">1.0</text>
            <text x="220" y="345" class="schematic__label schematic__label--small">2.0</text>
            <text x="320" y="345" class="schematic__label schematic__label--small">3.0</text>
            <text x="80" y="138" class="schematic__label schematic__label--small">1.1</text>
            <text x="160" y="138" class="schematic__label schematic__label--small">1.2</text>
            <text x="190" y="138" class="schematic__label schematic__label--small">2.1</text>
            <text x="250" y="138" class="schematic__label schematic__label--small">2.2</text>
            <text x="290" y="138" class="schematic__label schematic__label--small">3.1</text>
            <text x="360" y="138" class="schematic__label schematic__label--small">3.2</text>

            <!-- root marker -->
            <circle cx="220" cy="430" r="2.5" class="schematic__node" />
          </svg>
        </figure>
      </div>

      <div class="hero__floor">
        <span aria-hidden="true">↓</span>
        <span>SCROLL TO CONTINUE / 向下滚动</span>
      </div>
    </section>

    <!-- ============ §01 SELECTION / FEATURED ============ -->
    <div class="section-divider">
      <span class="section-divider__num">§01</span>
      <span class="section-divider__rule" />
      <span class="section-divider__label">SELECTION INDEX</span>
    </div>

    <DiscoveryRail
      kicker="§01 / Selection index"
      title="编辑标记节点"
      description="由管理员从近期分岔中标记的少量节点。如果暂无路径偏好，建议从此进入。"
      :items="featuredItems"
      :loading="featuredLoading"
      :error="featuredError as Error | null"
      empty-text="暂无标记条目。"
      action-label="进入档案"
      action-to="/books"
    />

    <!-- ============ §02 RECENT ============ -->
    <div class="section-divider">
      <span class="section-divider__num">§02</span>
      <span class="section-divider__rule" />
      <span class="section-divider__label">RECENT ENTRIES</span>
    </div>

    <DiscoveryRail
      kicker="§02 / Recent entries"
      title="近期入档节点"
      description="近期已发布的新节点，按入档时间倒序排列。每一条都可能成为新世界线的根。"
      :items="latestFeedItems"
      :loading="latestFeedLoading"
      :error="latestFeedError as Error | null"
      empty-text="尚无近期入档。"
      action-label="查看完整目录"
      action-to="/books"
    />

    <!-- ============ §03 STRUCTURAL NOTES ============ -->
    <div class="section-divider">
      <span class="section-divider__num">§03</span>
      <span class="section-divider__rule" />
      <span class="section-divider__label">STRUCTURAL NOTES</span>
    </div>

    <section class="notes">
      <div class="notes__head">
        <h2 class="notes__title">关于本档案</h2>
        <p class="notes__lede">
          以下三条说明了档案的结构边界与协作机制。阅读不需要登记身份；写入需要。
        </p>
      </div>

      <ol class="notes__list">
        <li class="notes__item">
          <span class="notes__num">3.1</span>
          <div class="notes__body">
            <h3 class="notes__head3">树状结构</h3>
            <p class="notes__text">
              一本书不是线性的章节序列，而是一棵节点树。每个节点是一个独立的叙述单元，可继续分裂为多条后续分支。
            </p>
          </div>
        </li>

        <li class="notes__item">
          <span class="notes__num">3.2</span>
          <div class="notes__body">
            <h3 class="notes__head3">分支续写</h3>
            <p class="notes__text">
              观测者可以选择任意已发布节点，在该节点之后建立新的子节点。新节点会作为该路径的一条分支并入树。
            </p>
          </div>
        </li>

        <li class="notes__item">
          <span class="notes__num">3.3</span>
          <div class="notes__body">
            <h3 class="notes__head3">入档审阅</h3>
            <p class="notes__text">
              新建分支须经管理员审阅后才会入档（status: PUB）。在此之前，节点状态为 PEND，仅作者本人可见。
            </p>
          </div>
        </li>
      </ol>
    </section>

    <!-- ============ §04 ATTENTION / TRENDING ============ -->
    <div class="section-divider">
      <span class="section-divider__num">§04</span>
      <span class="section-divider__rule" />
      <span class="section-divider__label">ATTENTION / 收到点赞最多</span>
    </div>

    <DiscoveryRail
      kicker="§04 / Attention"
      title="收到点赞最多的节点"
      description="按点赞数排序：优先取近七日发布的；近期内容不足时退到全时榜。"
      :items="trendingItems"
      :loading="trendingLoading"
      :error="trendingError as Error | null"
      empty-text="尚无点赞记录。"
    />

    <!-- ============ §05 QUERY ============ -->
    <div class="section-divider">
      <span class="section-divider__num">§05</span>
      <span class="section-divider__rule" />
      <span class="section-divider__label">QUERY / 标题与正文搜索</span>
    </div>

    <section class="query">
      <div class="query__head">
        <h2 class="query__title">查询已发布节点</h2>
        <p class="query__lede">
          按关键词检索已入档的节点（标题与正文）。区分大小写不敏感；暂不支持作者名搜索。
        </p>
      </div>

      <div class="query__field">
        <n-input
          v-model:value="searchKeyword"
          clearable
          placeholder="输入关键词，例如：雨 / 剑 / 信件"
          class="query__input"
          size="large"
        />
      </div>

      <div v-if="normalizedSearchKeyword.length === 0" class="query__hint">
        STATUS: <span>IDLE</span> · 输入关键词以触发查询
      </div>
      <div v-else-if="searchLoading" class="query__loading">
        <n-spin size="small" /><span class="query__loading-text">QUERYING…</span>
      </div>
      <div v-else-if="searchError" class="query__error">
        ERROR: {{ (searchError as Error).message }}
      </div>
      <div v-else-if="!searchResults?.length" class="query__hint">
        STATUS: <span>NO MATCH</span> · 未匹配到已发布节点
      </div>
      <div v-else>
        <p class="query__result-count">
          MATCHED {{ searchResults.length }} ENTR{{ searchResults.length === 1 ? 'Y' : 'IES' }}
        </p>
        <div class="query__results">
          <DiscoveryNodeCard
            v-for="item in searchItems"
            :key="`search-${item.id}`"
            :item="item"
          />
        </div>
      </div>
    </section>

    <!-- ============ §06 ENTER ============ -->
    <div class="section-divider">
      <span class="section-divider__num">§06</span>
      <span class="section-divider__rule" />
      <span class="section-divider__label">ENTER</span>
    </div>

    <section class="finale">
      <div class="finale__inner">
        <h2 class="finale__title">进入档案</h2>
        <p class="finale__lede">
          所有节点的入口都在故事册列表。从此进入。
        </p>
        <div class="finale__actions">
          <n-button class="finale__cta" size="large" @click="goTo('/books')">
            打开故事册列表
            <span class="finale__cta-arrow" aria-hidden="true">→</span>
          </n-button>
        </div>
        <p class="finale__signoff">
          — END OF FRONTPAGE / §00.01
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ─────────────────────────────────────────────
   Layout shell
   ───────────────────────────────────────────── */
.home {
  display: flex;
  flex-direction: column;
  gap: clamp(48px, 6vw, 88px);
  padding-bottom: 96px;
}

/* ─────────────────────────────────────────────
   §00 HERO / DOSSIER
   ───────────────────────────────────────────── */
.hero {
  position: relative;
  padding: clamp(28px, 4vw, 56px) clamp(28px, 6vw, 96px) clamp(60px, 7vw, 96px);
  border-bottom: 1px solid var(--line-strong);
  background: var(--bg-canvas);
  isolation: isolate;
}

/* Top metadata strip — like a manila folder header */
.hero__strip {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 24px;
  padding-bottom: 14px;
  margin-bottom: clamp(40px, 6vw, 72px);
  border-bottom: 1px solid var(--line-faint);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.hero__strip-cell--right {
  text-align: right;
}

/* Draft resume banner — sits between strip and hero body */
.hero__draft {
  margin-bottom: clamp(28px, 4vw, 48px);
  padding: 18px 22px;
  border: 1px solid var(--line-soft);
  background: var(--bg-shell);
  display: grid;
  gap: 10px;
  position: relative;
}

.hero__draft::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--text-primary);
}

.hero__draft-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: baseline;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.hero__draft-tag {
  color: var(--text-primary);
}

.hero__draft-locator {
  color: var(--text-secondary);
}

.hero__draft-time {
  margin-left: auto;
}

.hero__draft-preview {
  margin: 0;
  font-family: var(--font-body);
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

.hero__draft-title {
  color: var(--text-primary);
  font-weight: 500;
}

.hero__draft-snippet {
  color: var(--text-muted);
}

.hero__draft-cta {
  justify-self: start;
  background: var(--text-primary);
  border: 0;
  padding: 10px 18px;
  font-family: var(--font-body);
  font-size: 0.92rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: #050505;
  cursor: pointer;
  border-radius: 2px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: background var(--transition-base);
}

.hero__draft-cta:hover {
  background: #ffffff;
}

.hero__draft-cta span {
  transition: transform var(--transition-base);
}

.hero__draft-cta:hover span {
  transform: translateX(3px);
}

.hero__inner {
  position: relative;
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: clamp(40px, 5vw, 80px);
  align-items: start;
}

@media (min-width: 940px) {
  .hero__inner {
    grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  }
}

.hero__copy {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 640px;
}

.hero__kicker {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--text-faint);
  opacity: 0;
  animation: fade-up 0.6s ease 0.05s forwards;
}

.hero__title {
  display: inline-flex;
  align-items: baseline;
  gap: 0.04em;
  margin: 0;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(5rem, 12vw, 10.5rem);
  line-height: 0.92;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}

.hero__title-glyph {
  display: inline-block;
  opacity: 0;
  animation: fade-up 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.hero__title-glyph--1 {
  animation-delay: 0.15s;
}

.hero__title-glyph--2 {
  animation-delay: 0.3s;
  color: var(--text-secondary);
}

.hero__sub {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--text-faint);
  opacity: 0;
  animation: fade-up 0.6s ease 0.45s forwards;
}

.hero__lead {
  margin: 0;
  max-width: 540px;
  font-family: var(--font-body);
  font-size: clamp(1rem, 1.15vw, 1.08rem);
  line-height: 1.78;
  color: var(--text-secondary);
  opacity: 0;
  animation: fade-up 0.6s ease 0.6s forwards;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 22px;
  margin-top: 4px;
  opacity: 0;
  animation: fade-up 0.6s ease 0.75s forwards;
}

/* Buttons — flat, monochrome, square corners but tiny radius */
.hero__cta {
  --n-color: var(--text-primary) !important;
  --n-color-hover: #ffffff !important;
  --n-color-pressed: #d8d8d8 !important;
  --n-text-color: #050505 !important;
  --n-text-color-hover: #050505 !important;
  --n-text-color-pressed: #050505 !important;
  --n-border: none !important;
  --n-border-hover: none !important;
  font-family: var(--font-body) !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  height: 52px !important;
  padding: 0 28px !important;
  border-radius: 2px !important;
}

.hero__cta-arrow {
  display: inline-block;
  margin-left: 8px;
  transition: transform var(--transition-base);
}

.hero__cta:hover .hero__cta-arrow {
  transform: translateX(3px);
}

.hero__cta-link {
  background: none;
  border: 0;
  padding: 0 0 4px;
  font-family: var(--font-mono);
  font-size: 0.86rem;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 1px solid var(--line-soft);
  transition: color var(--transition-base), border-color var(--transition-base);
}

.hero__cta-link:hover {
  color: var(--text-primary);
  border-bottom-color: var(--text-primary);
}

/* Telemetry: real counts presented as a clinical row */
.hero__telemetry {
  margin: 12px 0 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  border-top: 1px solid var(--line-faint);
  border-bottom: 1px solid var(--line-faint);
  opacity: 0;
  animation: fade-up 0.6s ease 0.9s forwards;
}

.hero__telem {
  margin: 0;
  padding: 14px 16px 14px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-right: 1px solid var(--line-faint);
}

.hero__telem:last-child {
  border-right: 0;
}

.hero__telem dt {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.hero__telem dd {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 1.6rem;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  font-feature-settings: "tnum" 1;
}

/* Schematic dendrogram — orthogonal, no glow, monochrome */
.hero__schematic {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border: 1px solid var(--line-faint);
  background: var(--bg-shell);
  opacity: 0;
  animation: fade-in 0.8s ease 0.35s forwards;
}

.hero__schematic-caption {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.schematic {
  width: 100%;
  height: auto;
  max-height: 460px;
}

.schematic__grid line {
  stroke: var(--line-faint);
  stroke-width: 1;
}

.schematic__line {
  stroke: var(--text-secondary);
  stroke-width: 1.2;
  stroke-linecap: square;
  fill: none;
  stroke-dasharray: 200;
  stroke-dashoffset: 200;
  animation: draw 1.4s ease 0.4s forwards;
}

.schematic__line--trunk {
  stroke: var(--text-primary);
  stroke-width: 1.5;
  animation-delay: 0.2s;
}

.schematic__tick {
  stroke: var(--text-secondary);
  stroke-width: 1.2;
  stroke-linecap: square;
  opacity: 0;
  animation: fade-in 0.4s ease 1.5s forwards;
}

.schematic__node {
  fill: var(--text-primary);
}

.schematic__label {
  font-family: var(--font-mono);
  font-size: 11px;
  fill: var(--text-faint);
  letter-spacing: 0.04em;
  text-anchor: middle;
  opacity: 0;
  animation: fade-in 0.4s ease 1.7s forwards;
}

.schematic__label--small {
  font-size: 9.5px;
}

/* Floor: scroll cue */
.hero__floor {
  margin-top: clamp(40px, 5vw, 64px);
  display: flex;
  align-items: center;
  gap: 14px;
  padding-top: 16px;
  border-top: 1px solid var(--line-faint);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--text-faint);
}

/* ─────────────────────────────────────────────
   Section dividers (used between sections)
   ───────────────────────────────────────────── */
.section-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 clamp(24px, 6vw, 96px);
  margin-top: clamp(20px, 3vw, 32px);
  margin-bottom: -16px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.section-divider__num {
  color: var(--text-secondary);
}

.section-divider__rule {
  flex: 1;
  height: 1px;
  background: var(--line-faint);
}

.section-divider__label {
  color: var(--text-faint);
}

/* ─────────────────────────────────────────────
   §03 STRUCTURAL NOTES
   ───────────────────────────────────────────── */
.notes {
  padding: 0 clamp(24px, 6vw, 96px);
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.notes__head {
  max-width: 720px;
  margin-bottom: 36px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--line-faint);
}

.notes__title {
  margin: 0 0 12px;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(1.8rem, 3.4vw, 2.8rem);
  line-height: 1.18;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.notes__lede {
  margin: 0;
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.7;
  color: var(--text-secondary);
}

.notes__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  border-top: 1px solid var(--line-faint);
}

.notes__item {
  display: grid;
  grid-template-columns: minmax(64px, 96px) 1fr;
  gap: clamp(16px, 3vw, 40px);
  align-items: start;
  padding: 28px 0;
  border-bottom: 1px solid var(--line-faint);
}

.notes__num {
  font-family: var(--font-mono);
  font-size: 0.92rem;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  font-feature-settings: "tnum" 1;
}

.notes__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 720px;
}

.notes__head3 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: 1.2rem;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.notes__text {
  margin: 0;
  font-family: var(--font-body);
  font-size: 0.98rem;
  line-height: 1.72;
  color: var(--text-secondary);
}

/* ─────────────────────────────────────────────
   §05 QUERY
   ───────────────────────────────────────────── */
.query {
  padding: 0 clamp(24px, 6vw, 96px);
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.query__head {
  max-width: 640px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line-faint);
}

.query__title {
  margin: 0 0 10px;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(1.6rem, 3vw, 2.4rem);
  line-height: 1.16;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.query__lede {
  margin: 0;
  font-family: var(--font-body);
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--text-secondary);
}

.query__field {
  margin-bottom: 24px;
}

.query__input {
  --n-height: 52px !important;
  max-width: 640px;
}

.query__input :deep(.n-input__input-el) {
  font-family: var(--font-mono) !important;
  font-size: 0.95rem !important;
  letter-spacing: 0.02em;
}

.query__input :deep(.n-input__placeholder) {
  font-family: var(--font-mono) !important;
  letter-spacing: 0.02em;
}

.query__hint,
.query__error,
.query__loading,
.query__result-count {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
  padding: 12px 0;
}

.query__hint span {
  color: var(--text-secondary);
}

.query__error {
  color: var(--state-danger);
}

.query__loading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.query__loading-text {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.query__result-count {
  color: var(--text-secondary);
  border-bottom: 1px solid var(--line-faint);
  margin-bottom: 16px;
}

.query__results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

/* ─────────────────────────────────────────────
   §06 FINALE
   ───────────────────────────────────────────── */
.finale {
  padding: clamp(48px, 7vw, 96px) clamp(24px, 6vw, 96px);
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  border-top: 1px solid var(--line-faint);
  border-bottom: 1px solid var(--line-faint);
}

.finale__inner {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 720px;
}

.finale__title {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(2rem, 4vw, 3.2rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.finale__lede {
  margin: 0 0 12px;
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.7;
  color: var(--text-secondary);
}

.finale__actions {
  display: flex;
}

.finale__cta {
  --n-color: transparent !important;
  --n-color-hover: var(--bg-panel) !important;
  --n-color-pressed: var(--bg-panel-alt) !important;
  --n-text-color: var(--text-primary) !important;
  --n-text-color-hover: var(--text-primary) !important;
  --n-text-color-pressed: var(--text-primary) !important;
  --n-border: 1px solid var(--text-primary) !important;
  --n-border-hover: 1px solid var(--text-primary) !important;
  font-family: var(--font-body) !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  height: 52px !important;
  padding: 0 28px !important;
  border-radius: 2px !important;
}

.finale__cta-arrow {
  display: inline-block;
  margin-left: 8px;
  transition: transform var(--transition-base);
}

.finale__cta:hover .finale__cta-arrow {
  transform: translateX(3px);
}

.finale__signoff {
  margin: 24px 0 0;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--text-faint);
}

/* ─────────────────────────────────────────────
   Animations
   ───────────────────────────────────────────── */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes draw {
  to { stroke-dashoffset: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .hero__kicker,
  .hero__title-glyph,
  .hero__sub,
  .hero__lead,
  .hero__actions,
  .hero__telemetry,
  .hero__schematic {
    opacity: 1;
    animation: none !important;
    transform: none !important;
  }

  .schematic__line,
  .schematic__line--trunk,
  .schematic__tick,
  .schematic__label {
    stroke-dashoffset: 0;
    opacity: 1;
    animation: none !important;
  }
}
</style>
