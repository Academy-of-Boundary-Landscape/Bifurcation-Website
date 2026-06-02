<script setup lang="ts">
import { computed, ref } from 'vue'
import { NButton, NSpin } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useBooksQuery } from '@/features/story/queries'

const router = useRouter()
const { data: books, isLoading, error } = useBooksQuery()

const phaseOptions = [
  { label: '全部', value: 'all' },
  { label: '草稿阶段', value: 'drafting' },
  { label: '写作中', value: 'writing' },
  { label: '展示中', value: 'showcase' },
  { label: '已归档', value: 'archived' },
]

const selectedPhase = ref('all')

const filteredBooks = computed(() => {
  const items = books.value?.items
  if (!items) {
    return []
  }

  if (selectedPhase.value === 'all') {
    return items
  }

  return items.filter((book) => book.phase === selectedPhase.value)
})

function getPhaseLabel(phase?: string | null) {
  const labels: Record<string, string> = {
    drafting: '草稿阶段',
    writing: '写作中',
    showcase: '展示中',
    archived: '已归档',
  }

  if (!phase) {
    return '未标记'
  }

  return labels[phase] ?? phase
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('zh-CN')
}

function openBookDetail(bookId: number) {
  void router.push(`/books/${bookId}`)
}
</script>

<template>
  <div class="ui-page-stack">
    <section class="ui-page-hero ui-shell-panel ui-shell-grid">
      <div class="ui-page-hero__grid book-list-hero">
        <div>
          <p class="ui-shell-kicker">Archive Index</p>
          <h1 class="ui-shell-title book-list-hero__title">故事册列表</h1>
          <p class="ui-page-hero__lead">
            这里不是普通卡片墙，而是整套叙事系统的档案入口。先选定一部作品，再进入它的故事树导航台，决定从哪条路径开始阅读或创作。
          </p>
        </div>

        <div class="book-list-hero__metrics">
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Books</p>
            <p class="ui-metric-card__value">{{ books?.total ?? 0 }}</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Filter</p>
            <p class="ui-metric-card__value">{{ selectedPhase === 'all' ? 'All' : getPhaseLabel(selectedPhase) }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Phase Filter</p>
          <h2 class="ui-shell-title">筛选视图</h2>
          <p class="ui-page-section__lead">
            先按阶段缩小范围，再进入具体故事树。这里的筛选不追求复杂，只做最核心的浏览分流。
          </p>
        </div>
      </div>

      <div class="ui-filter-row">
        <n-button
          v-for="option in phaseOptions"
          :key="option.value"
          :type="selectedPhase === option.value ? 'primary' : 'default'"
          :ghost="selectedPhase !== option.value"
          @click="selectedPhase = option.value"
        >
          {{ option.label }}
        </n-button>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Story Archives</p>
          <h2 class="ui-shell-title">可进入的故事册</h2>
          <p class="ui-page-section__lead">
            每张卡片都只保留必要信息：标题、阶段、描述与入口。真正的结构探索将在书页里的故事树工作区完成。
          </p>
        </div>
      </div>

      <div v-if="isLoading" class="book-list-state">
        <n-spin size="large" />
      </div>

      <div v-else-if="error" class="ui-status-note ui-status-note--danger">
        加载失败：{{ (error as Error).message }}
      </div>

      <div v-else-if="filteredBooks.length === 0" class="ui-status-note">
        当前筛选条件下暂无故事册。
      </div>

      <div v-else class="ui-card-list ui-card-list--books">
        <article
          v-for="book in filteredBooks"
          :key="book.id"
          class="ui-archive-card ui-panel-section"
        >
          <div class="ui-archive-card__header">
            <div>
              <h3 class="ui-archive-card__title">{{ book.title }}</h3>
            </div>
            <span class="ui-chip">{{ getPhaseLabel(book.phase) }}</span>
          </div>

          <p class="ui-archive-card__lead">
            {{ book.description || '暂无描述。' }}
          </p>

          <div class="ui-archive-card__meta">
            <span>Created {{ formatDate(book.created_at) }}</span>
            <span>ID {{ book.id }}</span>
          </div>

          <div class="ui-archive-card__footer">
            <span class="book-list-card__hint">进入后可查看整棵故事树、节点检视器与分支阅读入口。</span>
            <n-button type="primary" @click="openBookDetail(book.id)">
              打开故事树
            </n-button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.book-list-hero {
  align-items: end;
}

.book-list-hero__title {
  font-size: clamp(2.2rem, 4vw, 3.4rem);
}

.book-list-hero__metrics {
  display: grid;
  gap: 14px;
}

.book-list-state {
  display: flex;
  justify-content: center;
  padding: 56px 0;
}

.book-list-card__hint {
  color: var(--text-faint);
  font-size: 13px;
  line-height: 1.75;
}

@media (min-width: 980px) {
  .book-list-hero {
    grid-template-columns: minmax(0, 2fr) minmax(260px, 0.9fr);
  }
}
</style>
