<script setup lang="ts">
import { computed, ref } from 'vue'
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
import { useAuthStore } from '@/stores/auth'
import type { DiscoveryRailItem } from '@/types/discovery'

const router = useRouter()
const authStore = useAuthStore()

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
    meta: options?.meta ?? [`${node.author.username}`, formatDate(node.published_at || node.created_at)],
    metrics: options?.metrics,
    hint: options?.hint ?? `Book ${node.book_id} · 节点 ${node.id}`,
    action: {
      label: options?.actionLabel ?? '阅读',
      to: `/story/node/${node.id}`,
    },
  }
}

const featuredItems = computed(() =>
  (featuredNodes.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: node.feature_rank ? `№${node.feature_rank}` : '精选',
      badgeTone: 'strong',
      metrics: [
        { label: '喜欢', value: String(node.likes_count) },
        { label: '续写', value: String(node.children_count) },
      ],
      hint: `Book ${node.book_id}`,
      actionLabel: '进入这条世界线',
      meta: [`${node.author.username}`, formatDate(node.published_at || node.created_at)],
    }),
  ),
)

const latestFeedItems = computed(() =>
  (latestFeed.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      actionLabel: '阅读',
    }),
  ),
)

const trendingItems = computed(() =>
  (trendingNodes.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: `${node.likes_count} 个心跳`,
      badgeTone: 'strong',
      metrics: [
        { label: '续写', value: String(node.children_count) },
        { label: '回声', value: String(node.comments_count) },
      ],
      hint: `${node.author.username}`,
      actionLabel: '在这里停留',
      meta: [formatDate(node.published_at || node.created_at)],
    }),
  ),
)

const searchItems = computed(() =>
  (searchResults.value ?? []).map((node) =>
    toDiscoveryItem(node, {
      badge: `Book ${node.book_id}`,
      hint: formatDate(node.published_at || node.created_at),
      actionLabel: '打开',
      meta: [`${node.author.username}`, `${node.likes_count} 个心跳`],
    }),
  ),
)

function goTo(path: string) {
  void router.push(path)
}
</script>

<template>
  <div class="home">
    <!-- ============ HERO ============ -->
    <section class="hero">
      <div class="hero__grain" aria-hidden="true" />

      <div class="hero__inner">
        <div class="hero__copy">
          <p class="hero__epigraph">
            <span class="hero__quote-mark" aria-hidden="true">“</span>
            时间在不停地分岔，<br>
            通向无数未来。
            <span class="hero__epigraph-attr">— Borges, 1941</span>
          </p>

          <h1 class="hero__title">
            <span class="hero__title-glyph hero__title-glyph--1">分</span><span class="hero__title-glyph hero__title-glyph--2">岔</span>
          </h1>

          <p class="hero__subline">Bifurcation</p>

          <p class="hero__lead">
            一片可以共同栽种的故事树。
            从任何一段叙述出发，沿原路读下去——
            <em>或者，在分歧处转身。</em>
          </p>

          <div class="hero__actions">
            <n-button class="hero__cta hero__cta--primary" size="large" @click="goTo('/books')">
              翻开
              <span class="hero__cta-arrow" aria-hidden="true">→</span>
            </n-button>
            <button v-if="!authStore.isAuthenticated" class="hero__cta-link" type="button" @click="goTo('/login')">
              在某个分歧处续写
            </button>
            <button v-else class="hero__cta-link" type="button" @click="goTo('/notifications')">
              查看新分支
            </button>
          </div>
        </div>

        <div class="hero__visual" aria-hidden="true">
          <svg viewBox="0 0 400 480" preserveAspectRatio="xMidYMid meet" class="hero-tree">
            <defs>
              <radialGradient id="hero-tree-glow" cx="50%" cy="100%" r="80%">
                <stop offset="0%" stop-color="rgba(200, 169, 106, 0.42)" />
                <stop offset="100%" stop-color="rgba(200, 169, 106, 0)" />
              </radialGradient>
            </defs>

            <!-- ambient glow at root -->
            <ellipse cx="200" cy="460" rx="180" ry="40" fill="url(#hero-tree-glow)" />

            <!-- trunk -->
            <path d="M200 460 L200 280" class="hero-tree__line hero-tree__line--trunk" />

            <!-- primary branches -->
            <path d="M200 280 Q160 240 110 200" class="hero-tree__line" style="--delay: 0.4s;" />
            <path d="M200 280 Q240 240 290 200" class="hero-tree__line" style="--delay: 0.5s;" />
            <path d="M200 280 Q200 220 200 160" class="hero-tree__line" style="--delay: 0.6s;" />

            <!-- secondary branches: left -->
            <path d="M110 200 Q70 170 40 130" class="hero-tree__line" style="--delay: 0.9s;" />
            <path d="M110 200 Q120 160 130 110" class="hero-tree__line" style="--delay: 1s;" />

            <!-- secondary: center -->
            <path d="M200 160 Q170 130 150 90" class="hero-tree__line" style="--delay: 1.1s;" />
            <path d="M200 160 Q230 130 250 90" class="hero-tree__line" style="--delay: 1.2s;" />

            <!-- secondary: right -->
            <path d="M290 200 Q310 160 320 110" class="hero-tree__line" style="--delay: 1.1s;" />
            <path d="M290 200 Q340 170 360 130" class="hero-tree__line" style="--delay: 1.2s;" />

            <!-- leaves at the tip of each terminal branch -->
            <circle cx="40" cy="130" r="3" class="hero-tree__leaf" style="--delay: 1.6s;" />
            <circle cx="130" cy="110" r="3" class="hero-tree__leaf" style="--delay: 1.7s;" />
            <circle cx="150" cy="90" r="3" class="hero-tree__leaf" style="--delay: 1.8s;" />
            <circle cx="250" cy="90" r="3" class="hero-tree__leaf" style="--delay: 1.9s;" />
            <circle cx="320" cy="110" r="3" class="hero-tree__leaf" style="--delay: 2s;" />
            <circle cx="360" cy="130" r="3" class="hero-tree__leaf" style="--delay: 2.1s;" />

            <!-- root marker -->
            <circle cx="200" cy="460" r="4" class="hero-tree__root" />
          </svg>
        </div>
      </div>

      <div class="hero__floor">
        <span class="hero__floor-mark" aria-hidden="true">↓</span>
        <span>滚动以进入</span>
      </div>
    </section>

    <!-- ============ TRANSITION QUOTE ============ -->
    <section class="quote-transition">
      <p class="quote-transition__text">
        在每一个停顿处，<br>故事都可以<em>再次开始</em>。
      </p>
    </section>

    <!-- ============ FEATURED ============ -->
    <DiscoveryRail
      kicker="By the editors"
      title="编辑选出的几条小径"
      description="管理员从近期分岔中标记的少数节点。如果你不知道从哪里开始，从这里。"
      :items="featuredItems"
      :loading="featuredLoading"
      :error="featuredError as Error | null"
      empty-text="本月还没有被光标记的节点。先翻开故事册看看。"
      action-label="去往故事册"
      action-to="/books"
    />

    <!-- ============ LATEST ============ -->
    <DiscoveryRail
      kicker="Recent whispers"
      title="今日的回声"
      description="刚刚发生的续写。每一个都可能延伸出新的小径。"
      :items="latestFeedItems"
      :loading="latestFeedLoading"
      :error="latestFeedError as Error | null"
      empty-text="今天还没有新的回声。"
      action-label="查看全部"
      action-to="/books"
    />

    <!-- ============ ABOUT (lyrical, not specs) ============ -->
    <section class="about">
      <div class="about__inner">
        <div class="about__lede">
          <p class="about__kicker">关于这个地方</p>
          <h2 class="about__title">
            像树一样生长的<br>故事
          </h2>
        </div>

        <div class="about__body">
          <p class="about__paragraph">
            这里没有线性的"下一章"。每个段落都可能成为新的根，每个停顿都允许另一种走法。
            你可以静静地从一棵树的根读到某片叶子，<em>或者，在某条枝丫处转身，写下你看到的另一个版本。</em>
          </p>

          <ul class="about__points">
            <li>
              <span class="about__point-mark" aria-hidden="true">树</span>
              <span>不是单线小说。整本书是一棵会分裂的树。</span>
            </li>
            <li>
              <span class="about__point-mark" aria-hidden="true">续</span>
              <span>在任何节点处续写，都会成为这条世界线的一个分支。</span>
            </li>
            <li>
              <span class="about__point-mark" aria-hidden="true">审</span>
              <span>新加入的分支会先经过审阅，发布后正式接入树。</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ============ TRENDING ============ -->
    <DiscoveryRail
      kicker="Attending"
      title="许多人正在停留的分歧"
      description="近七日被反复打开、点赞、续写的节点。"
      :items="trendingItems"
      :loading="trendingLoading"
      :error="trendingError as Error | null"
      empty-text="还没有形成集中的关注。"
    />

    <!-- ============ SEARCH ============ -->
    <section class="search">
      <div class="search__head">
        <p class="search__kicker">Find a path</p>
        <h2 class="search__title">找到一个开始的地方</h2>
        <p class="search__lead">
          输入一个词、一个名字、一个画面——平台会从已发布的节点里找到匹配。
        </p>
      </div>

      <div class="search__field">
        <n-input
          v-model:value="searchKeyword"
          clearable
          placeholder="比如「雨」「剑」「她回头」"
          class="search__input"
          size="large"
        />
      </div>

      <div v-if="normalizedSearchKeyword.length === 0" class="search__hint">
        输入关键词后，结果会出现在下方。
      </div>
      <div v-else-if="searchLoading" class="search__loading">
        <n-spin size="medium" />
      </div>
      <div v-else-if="searchError" class="search__error">
        搜索失败：{{ (searchError as Error).message }}
      </div>
      <div v-else-if="!searchResults?.length" class="search__hint">
        没有匹配的节点。换个词试试？
      </div>
      <div v-else class="search__results">
        <DiscoveryNodeCard
          v-for="item in searchItems"
          :key="`search-${item.id}`"
          :item="item"
        />
      </div>
    </section>

    <!-- ============ FINAL CTA ============ -->
    <section class="finale">
      <div class="finale__inner">
        <p class="finale__kicker">从这里开始</p>
        <h2 class="finale__title">
          <em>翻开</em>第一页。
        </h2>
        <p class="finale__lead">
          一切都从故事册开始。挑一棵树，进入它的根。
        </p>
        <n-button class="finale__cta" size="large" @click="goTo('/books')">
          打开故事册
          <span class="finale__cta-arrow" aria-hidden="true">→</span>
        </n-button>
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
  gap: clamp(60px, 8vw, 110px);
  padding-bottom: 96px;
}

/* ─────────────────────────────────────────────
   HERO
   ───────────────────────────────────────────── */
.hero {
  position: relative;
  min-height: min(820px, 92vh);
  padding: clamp(40px, 7vw, 96px) clamp(28px, 6vw, 96px) clamp(60px, 7vw, 96px);
  overflow: hidden;
  isolation: isolate;
  border-bottom: 1px solid var(--line-faint);
  background:
    radial-gradient(ellipse at 18% 110%, rgba(200, 169, 106, 0.07), transparent 55%),
    radial-gradient(ellipse at 88% 0%, rgba(200, 169, 106, 0.04), transparent 50%),
    var(--bg-canvas);
}

/* Subtle paper grain overlay */
.hero__grain {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.5;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.06 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: overlay;
}

.hero__inner {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: clamp(40px, 5vw, 80px);
  align-items: center;
}

@media (min-width: 880px) {
  .hero__inner {
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  }
}

.hero__copy {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 620px;
}

/* Epigraph: opens the page with a Borges quote */
.hero__epigraph {
  position: relative;
  margin: 0;
  padding-left: 22px;
  border-left: 1px solid var(--accent-amber);
  font-family: var(--font-serif);
  font-style: italic;
  font-weight: 300;
  font-size: clamp(0.95rem, 1.1vw, 1.05rem);
  line-height: 1.7;
  color: var(--text-secondary);
  opacity: 0;
  transform: translateY(8px);
  animation: fade-up 0.8s ease 0.1s forwards;
}

.hero__quote-mark {
  position: absolute;
  left: 8px;
  top: -16px;
  font-family: var(--font-serif);
  font-size: 3rem;
  line-height: 1;
  color: var(--accent-amber);
  opacity: 0.4;
}

.hero__epigraph-attr {
  display: block;
  margin-top: 6px;
  font-family: var(--font-mono);
  font-style: normal;
  font-size: 0.78rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-faint);
}

/* The massive title — uses Fraunces variable font opsz + WONK */
.hero__title {
  display: flex;
  align-items: baseline;
  gap: 0.06em;
  margin: 0;
  font-family: var(--font-serif);
  font-weight: 400;
  font-size: clamp(5.5rem, 14vw, 13rem);
  line-height: 0.92;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  font-variation-settings: "opsz" 144, "SOFT" 50;
}

.hero__title-glyph {
  display: inline-block;
  opacity: 0;
  animation: fade-up 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.hero__title-glyph--1 {
  animation-delay: 0.2s;
}

.hero__title-glyph--2 {
  animation-delay: 0.4s;
  color: var(--accent-amber);
  font-style: italic;
  font-variation-settings: "opsz" 144, "SOFT" 100, "WONK" 1;
}

.hero__subline {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.92rem;
  letter-spacing: 0.42em;
  text-transform: uppercase;
  color: var(--text-faint);
  opacity: 0;
  animation: fade-up 0.8s ease 0.6s forwards;
}

.hero__lead {
  margin: 0;
  max-width: 520px;
  font-family: var(--font-body);
  font-size: clamp(1.05rem, 1.3vw, 1.18rem);
  line-height: 1.75;
  color: var(--text-secondary);
  opacity: 0;
  animation: fade-up 0.8s ease 0.8s forwards;
}

.hero__lead em {
  font-family: var(--font-serif);
  font-style: italic;
  font-weight: 400;
  color: var(--accent-amber);
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 24px;
  margin-top: 12px;
  opacity: 0;
  animation: fade-up 0.8s ease 1s forwards;
}

/* Override Naive button color to amber */
.hero__cta {
  --n-color: var(--accent-amber) !important;
  --n-color-hover: #d6b97c !important;
  --n-color-pressed: #b8985c !important;
  --n-text-color: #1a1407 !important;
  --n-text-color-hover: #1a1407 !important;
  --n-text-color-pressed: #1a1407 !important;
  --n-border: none !important;
  --n-border-hover: none !important;
  font-family: var(--font-body) !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  height: 56px !important;
  padding: 0 32px !important;
  border-radius: 4px !important;
}

.hero__cta-arrow {
  display: inline-block;
  margin-left: 10px;
  transition: transform var(--transition-base);
}

.hero__cta:hover .hero__cta-arrow {
  transform: translateX(4px);
}

.hero__cta-link {
  background: none;
  border: 0;
  padding: 0 0 4px;
  font-family: var(--font-serif);
  font-style: italic;
  font-weight: 400;
  font-size: 1.05rem;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 1px solid var(--line-soft);
  transition: color var(--transition-base), border-color var(--transition-base);
}

.hero__cta-link:hover {
  color: var(--accent-amber);
  border-bottom-color: var(--accent-amber);
}

/* Visual — animated SVG branching tree */
.hero__visual {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 360px;
  opacity: 0;
  animation: fade-in 1.2s ease 0.5s forwards;
}

@media (max-width: 879px) {
  .hero__visual {
    min-height: 280px;
    margin-top: 16px;
  }
}

.hero-tree {
  width: 100%;
  max-width: 480px;
  height: auto;
  filter: drop-shadow(0 0 24px rgba(200, 169, 106, 0.15));
}

.hero-tree__line {
  fill: none;
  stroke: var(--accent-amber);
  stroke-width: 1.2;
  stroke-linecap: round;
  stroke-dasharray: 400;
  stroke-dashoffset: 400;
  animation: draw 1.6s cubic-bezier(0.6, 0, 0.4, 1) var(--delay, 0s) forwards;
  opacity: 0.85;
}

.hero-tree__line--trunk {
  stroke-width: 1.5;
}

.hero-tree__leaf {
  fill: var(--accent-amber);
  opacity: 0;
  transform-origin: center;
  animation:
    leaf-pulse 1.4s ease var(--delay, 0s) forwards,
    leaf-float 4s ease-in-out infinite calc(var(--delay, 0s) + 1.4s);
}

.hero-tree__root {
  fill: var(--accent-amber);
  animation: pulse 2.4s ease-in-out infinite;
}

/* Floor: scroll cue */
.hero__floor {
  position: absolute;
  left: 50%;
  bottom: clamp(20px, 3vw, 36px);
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--text-faint);
  opacity: 0;
  animation: fade-in 0.8s ease 1.6s forwards;
}

.hero__floor-mark {
  display: inline-block;
  animation: bob 2.4s ease-in-out infinite;
}

/* ─────────────────────────────────────────────
   Quote transition (centered lyrical sentence)
   ───────────────────────────────────────────── */
.quote-transition {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(40px, 8vw, 100px) 24px;
}

.quote-transition__text {
  margin: 0;
  text-align: center;
  font-family: var(--font-serif);
  font-weight: 300;
  font-size: clamp(1.8rem, 4.4vw, 3.4rem);
  line-height: 1.32;
  color: var(--text-primary);
  font-variation-settings: "opsz" 96, "SOFT" 50;
  max-width: 18ch;
}

.quote-transition__text em {
  font-style: italic;
  color: var(--accent-amber);
  font-variation-settings: "opsz" 96, "SOFT" 100, "WONK" 1;
}

/* ─────────────────────────────────────────────
   About (lyrical, replacing "principles" + "workflow")
   ───────────────────────────────────────────── */
.about {
  padding: 0 clamp(24px, 6vw, 96px);
}

.about__inner {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 48px;
}

@media (min-width: 880px) {
  .about__inner {
    grid-template-columns: minmax(0, 0.9fr) minmax(0, 1fr);
    gap: clamp(40px, 6vw, 96px);
    align-items: start;
  }
}

.about__kicker {
  margin: 0 0 16px;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--accent-amber);
}

.about__title {
  margin: 0;
  font-family: var(--font-serif);
  font-weight: 400;
  font-size: clamp(2.4rem, 5vw, 4rem);
  line-height: 1.06;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  font-variation-settings: "opsz" 144, "SOFT" 50;
}

.about__paragraph {
  margin: 0 0 32px;
  font-family: var(--font-body);
  font-size: clamp(1.05rem, 1.2vw, 1.18rem);
  line-height: 1.78;
  color: var(--text-secondary);
}

.about__paragraph em {
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--accent-amber);
  font-weight: 400;
}

.about__points {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.about__points li {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 16px 18px;
  background: var(--bg-panel);
  border: 1px solid var(--line-faint);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.98rem;
  line-height: 1.6;
  color: var(--text-secondary);
  transition: border-color var(--transition-base), background var(--transition-base);
}

.about__points li:hover {
  border-color: var(--accent-amber-soft);
  background: var(--bg-panel-alt);
}

.about__point-mark {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-serif);
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--accent-amber);
  background: var(--accent-amber-faint);
  border: 1px solid var(--accent-amber-soft);
  border-radius: 50%;
}

/* ─────────────────────────────────────────────
   Search
   ───────────────────────────────────────────── */
.search {
  padding: 0 clamp(24px, 6vw, 96px);
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.search__head {
  max-width: 640px;
  margin-bottom: 32px;
}

.search__kicker {
  margin: 0 0 14px;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--accent-amber);
}

.search__title {
  margin: 0 0 16px;
  font-family: var(--font-serif);
  font-weight: 400;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.12;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  font-variation-settings: "opsz" 96, "SOFT" 50;
}

.search__lead {
  margin: 0;
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.7;
  color: var(--text-secondary);
}

.search__field {
  margin-bottom: 32px;
}

.search__input {
  --n-height: 56px !important;
  max-width: 640px;
}

.search__input :deep(.n-input__input-el) {
  font-family: var(--font-serif) !important;
  font-style: italic;
  font-size: 1.1rem !important;
}

.search__hint,
.search__error {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 1rem;
  color: var(--text-muted);
  padding: 16px 0;
}

.search__error {
  color: var(--state-danger);
}

.search__loading {
  padding: 24px 0;
}

.search__results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

/* ─────────────────────────────────────────────
   Finale
   ───────────────────────────────────────────── */
.finale {
  position: relative;
  margin: 0 clamp(24px, 6vw, 96px);
  padding: clamp(60px, 9vw, 120px) clamp(36px, 6vw, 96px);
  border: 1px solid var(--accent-amber-soft);
  border-radius: var(--radius-md);
  background:
    radial-gradient(ellipse at 50% 100%, rgba(200, 169, 106, 0.08), transparent 70%),
    var(--bg-panel);
  text-align: center;
  overflow: hidden;
}

.finale::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.04 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: overlay;
  pointer-events: none;
}

.finale__inner {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  max-width: 640px;
  margin: 0 auto;
}

.finale__kicker {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--accent-amber);
}

.finale__title {
  margin: 0;
  font-family: var(--font-serif);
  font-weight: 400;
  font-size: clamp(2.6rem, 6vw, 4.6rem);
  line-height: 1.08;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  font-variation-settings: "opsz" 144, "SOFT" 50;
}

.finale__title em {
  font-style: italic;
  color: var(--accent-amber);
  font-variation-settings: "opsz" 144, "SOFT" 100, "WONK" 1;
}

.finale__lead {
  margin: 4px 0 24px;
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 1.15rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

.finale__cta {
  --n-color: transparent !important;
  --n-color-hover: var(--accent-amber-faint) !important;
  --n-color-pressed: var(--accent-amber-soft) !important;
  --n-text-color: var(--accent-amber) !important;
  --n-text-color-hover: var(--accent-amber) !important;
  --n-text-color-pressed: #d6b97c !important;
  --n-border: 1px solid var(--accent-amber) !important;
  --n-border-hover: 1px solid var(--accent-amber) !important;
  font-family: var(--font-body) !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  height: 56px !important;
  padding: 0 32px !important;
  border-radius: 4px !important;
}

.finale__cta-arrow {
  display: inline-block;
  margin-left: 10px;
  transition: transform var(--transition-base);
}

.finale__cta:hover .finale__cta-arrow {
  transform: translateX(4px);
}

/* ─────────────────────────────────────────────
   Animations
   ───────────────────────────────────────────── */
@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes draw {
  to { stroke-dashoffset: 0; }
}

@keyframes leaf-pulse {
  0%   { opacity: 0; transform: scale(0); }
  60%  { opacity: 1; transform: scale(1.4); }
  100% { opacity: 1; transform: scale(1); }
}

@keyframes leaf-float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-3px); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1);   opacity: 1; }
  50%      { transform: scale(1.4); opacity: 0.6; }
}

@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(4px); }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .hero__epigraph,
  .hero__title-glyph,
  .hero__subline,
  .hero__lead,
  .hero__actions,
  .hero__visual,
  .hero__floor {
    opacity: 1;
    animation: none !important;
    transform: none !important;
  }

  .hero-tree__line {
    stroke-dashoffset: 0;
    animation: none !important;
  }

  .hero-tree__leaf {
    opacity: 1;
    animation: none !important;
  }

  .hero-tree__root,
  .hero__floor-mark {
    animation: none !important;
  }
}
</style>
