<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDatePicker,
  NEmpty,
  NInput,
  NSelect,
  NSpin,
  NSwitch,
  NTag,
} from 'naive-ui'
import { useMessage } from 'naive-ui'

import type { BookPhase, StoryBookCreate } from '@/types/models'
import { useBooksQuery, useCreateBookMutation, useUpdateBookMutation } from '@/features/story/queries'

const message = useMessage()
const router = useRouter()

const { data: books, isLoading } = useBooksQuery()
const { mutate: createBook, isPending: creatingBook } = useCreateBookMutation()
const { mutate: updateBook, isPending: updatingBook } = useUpdateBookMutation()

const activeBookId = ref<number | null>(null)
const expandedBookId = ref<number | null>(null)
const editState = ref<
  Record<
    number,
    {
      title: string
      description: string
      cover_image: string
      phase: BookPhase
      allow_new_nodes: boolean
      start_at: number | null
      writing_end_at: number | null
      showcase_end_at: number | null
    }
  >
>({})

const phaseOptions: Array<{ label: string; value: BookPhase }> = [
  { label: '草稿阶段', value: 'drafting' },
  { label: '写作阶段', value: 'writing' },
  { label: '展示阶段', value: 'showcase' },
  { label: '归档阶段', value: 'archived' },
]

const createForm = ref<{
  title: string
  description: string
  cover_image: string
  phase: BookPhase
  allow_new_nodes: boolean
  start_at: number | null
  writing_end_at: number | null
  showcase_end_at: number | null
}>({
  title: '',
  description: '',
  cover_image: '',
  phase: 'drafting',
  allow_new_nodes: true,
  start_at: null,
  writing_end_at: null,
  showcase_end_at: null,
})

const sortedBooks = computed(() => [...(books.value ?? [])].sort((a, b) => b.id - a.id))

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

function getPhaseType(phase: BookPhase) {
  switch (phase) {
    case 'drafting':
      return 'warning'
    case 'writing':
      return 'primary'
    case 'showcase':
      return 'success'
    case 'archived':
      return 'default'
  }
}

function getPhaseLabel(phase: BookPhase) {
  switch (phase) {
    case 'drafting':
      return '草稿阶段'
    case 'writing':
      return '写作中'
    case 'showcase':
      return '展示中'
    case 'archived':
      return '已归档'
  }
}

function toIsoOrNull(value: number | null) {
  return value ? new Date(value).toISOString() : null
}

function toTimestampOrNull(value: string | null | undefined) {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
}

function resetCreateForm() {
  createForm.value = {
    title: '',
    description: '',
    cover_image: '',
    phase: 'drafting',
    allow_new_nodes: true,
    start_at: null,
    writing_end_at: null,
    showcase_end_at: null,
  }
}

function ensureEditState(book: NonNullable<typeof books.value>[number]) {
  if (editState.value[book.id]) return editState.value[book.id]
  editState.value = {
    ...editState.value,
    [book.id]: {
      title: book.title,
      description: book.description || '',
      cover_image: book.cover_image || '',
      phase: book.phase,
      allow_new_nodes: book.allow_new_nodes,
      start_at: toTimestampOrNull(book.start_at),
      writing_end_at: toTimestampOrNull(book.writing_end_at),
      showcase_end_at: toTimestampOrNull(book.showcase_end_at),
    },
  }
  return editState.value[book.id]
}

function toggleEditBook(book: NonNullable<typeof books.value>[number]) {
  if (expandedBookId.value === book.id) {
    expandedBookId.value = null
    return
  }
  ensureEditState(book)
  expandedBookId.value = book.id
}

function handleCreateBook() {
  if (!createForm.value.title.trim()) {
    message.error('请先填写故事册标题')
    return
  }

  const payload: StoryBookCreate = {
    title: createForm.value.title.trim(),
    description: createForm.value.description.trim() || null,
    cover_image: createForm.value.cover_image.trim() || null,
    phase: createForm.value.phase,
    allow_new_nodes: createForm.value.allow_new_nodes,
    start_at: toIsoOrNull(createForm.value.start_at),
    writing_end_at: toIsoOrNull(createForm.value.writing_end_at),
    showcase_end_at: toIsoOrNull(createForm.value.showcase_end_at),
  }

  createBook(payload, {
    onSuccess: () => {
      message.success('故事册创建成功')
      resetCreateForm()
    },
    onError: () => {
      message.error('故事册创建失败，请重试')
    },
  })
}

function updateBookPhase(bookId: number, phase: BookPhase) {
  activeBookId.value = bookId
  updateBook(
    { bookId, payload: { phase } },
    {
      onSuccess: () => {
        message.success('故事册阶段已更新')
      },
      onError: () => {
        message.error('更新阶段失败，请重试')
      },
      onSettled: () => {
        activeBookId.value = null
      },
    },
  )
}

function toggleBookCreation(bookId: number, allowNewNodes: boolean) {
  activeBookId.value = bookId
  updateBook(
    { bookId, payload: { allow_new_nodes: !allowNewNodes } },
    {
      onSuccess: () => {
        message.success('创作开关已更新')
      },
      onError: () => {
        message.error('更新创作开关失败，请重试')
      },
      onSettled: () => {
        activeBookId.value = null
      },
    },
  )
}

function handleSaveBook(bookId: number) {
  const draft = editState.value[bookId]
  if (!draft) return
  if (!draft.title.trim()) {
    message.error('故事册标题不能为空')
    return
  }

  activeBookId.value = bookId
  updateBook(
    {
      bookId,
      payload: {
        title: draft.title.trim(),
        description: draft.description.trim() || null,
        cover_image: draft.cover_image.trim() || null,
        phase: draft.phase,
        allow_new_nodes: draft.allow_new_nodes,
        start_at: toIsoOrNull(draft.start_at),
        writing_end_at: toIsoOrNull(draft.writing_end_at),
        showcase_end_at: toIsoOrNull(draft.showcase_end_at),
      },
    },
    {
      onSuccess: () => {
        message.success('故事册信息已更新')
      },
      onError: () => {
        message.error('更新故事册失败，请重试')
      },
      onSettled: () => {
        activeBookId.value = null
      },
    },
  )
}

function openBookDetail(bookId: number) {
  void router.push({ name: 'book-detail', params: { bookId } })
}
</script>

<template>
  <div class="ui-page-stack admin-page">
    <section class="ui-page-hero ui-shell-panel ui-shell-grid">
      <div class="ui-page-hero__grid admin-hero">
        <div>
          <p class="ui-shell-kicker">Admin / Books</p>
          <h1 class="ui-shell-title">故事册管理</h1>
          <p class="ui-page-hero__lead">
            管理员在这里创建新的故事册，控制创作阶段、创作开关和展示节奏。
          </p>
        </div>
        <div class="admin-hero__metrics">
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Total Books</p>
            <p class="ui-metric-card__value">{{ sortedBooks.length }}</p>
          </div>
          <div class="ui-metric-card">
            <p class="ui-metric-card__label">Writable</p>
            <p class="ui-metric-card__value">
              {{ sortedBooks.filter((book) => book.allow_new_nodes).length }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Create</p>
          <h2 class="ui-shell-title">新建故事册</h2>
          <p class="ui-page-section__lead">先定义标题、阶段和创作时间窗口，再发布给前台使用。</p>
        </div>
      </div>

      <div class="admin-form-grid">
        <label class="admin-field">
          <span class="admin-field__label">标题</span>
          <n-input v-model:value="createForm.title" placeholder="例如：玻璃海平线" />
        </label>

        <label class="admin-field admin-field--wide">
          <span class="admin-field__label">简介</span>
          <n-input
            v-model:value="createForm.description"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="简要说明这个故事册的主题、世界观和写作目标。"
          />
        </label>

        <label class="admin-field admin-field--wide">
          <span class="admin-field__label">封面链接</span>
          <n-input v-model:value="createForm.cover_image" placeholder="可选，填写封面图片 URL" />
        </label>

        <label class="admin-field">
          <span class="admin-field__label">初始阶段</span>
          <n-select v-model:value="createForm.phase" :options="phaseOptions" />
        </label>

        <label class="admin-field admin-field--switch">
          <span class="admin-field__label">允许新节点</span>
          <div class="admin-switch-row">
            <span class="admin-switch-row__hint">
              {{ createForm.allow_new_nodes ? '允许继续创作' : '暂时关闭创作' }}
            </span>
            <n-switch v-model:value="createForm.allow_new_nodes" />
          </div>
        </label>

        <label class="admin-field">
          <span class="admin-field__label">开始时间</span>
          <n-date-picker v-model:value="createForm.start_at" type="datetime" clearable />
        </label>

        <label class="admin-field">
          <span class="admin-field__label">写作截止</span>
          <n-date-picker v-model:value="createForm.writing_end_at" type="datetime" clearable />
        </label>

        <label class="admin-field">
          <span class="admin-field__label">展示截止</span>
          <n-date-picker v-model:value="createForm.showcase_end_at" type="datetime" clearable />
        </label>
      </div>

      <div class="admin-form-actions">
        <n-button ghost @click="resetCreateForm">重置</n-button>
        <n-button type="primary" :loading="creatingBook" @click="handleCreateBook">创建故事册</n-button>
      </div>
    </section>

    <section class="ui-page-section ui-shell-panel">
      <div class="ui-page-section__header">
        <div>
          <p class="ui-shell-kicker">Archive</p>
          <h2 class="ui-shell-title">故事册列表</h2>
          <p class="ui-page-section__lead">查看当前所有故事册，并快速切换阶段、开关创作入口或展开编辑完整信息。</p>
        </div>
      </div>

      <n-spin :show="isLoading">
        <n-empty v-if="!sortedBooks.length" description="当前还没有任何故事册" />

        <div v-else class="admin-book-list">
          <article
            v-for="book in sortedBooks"
            :key="book.id"
            class="admin-book-card ui-panel-section"
          >
            <div class="admin-book-card__header">
              <div>
                <h3 class="admin-book-card__title">{{ book.title }}</h3>
                <p class="admin-book-card__description">
                  {{ book.description || '暂无简介。' }}
                </p>
              </div>
              <div class="admin-book-card__badges">
                <n-tag :type="getPhaseType(book.phase)" size="small">{{ getPhaseLabel(book.phase) }}</n-tag>
                <n-tag size="small" :type="book.allow_new_nodes ? 'success' : 'default'">
                  {{ book.allow_new_nodes ? '开放创作' : '创作关闭' }}
                </n-tag>
              </div>
            </div>

            <div class="admin-book-card__meta">
              <span>创建时间：{{ formatDateTime(book.created_at) }}</span>
              <span>开始时间：{{ formatDateTime(book.start_at) }}</span>
              <span>写作截止：{{ formatDateTime(book.writing_end_at) }}</span>
              <span>展示截止：{{ formatDateTime(book.showcase_end_at) }}</span>
            </div>

            <div class="admin-book-card__actions">
              <n-button
                size="small"
                type="primary"
                @click="openBookDetail(book.id)"
              >
                查看故事树
              </n-button>

              <n-button
                size="small"
                ghost
                :loading="updatingBook && activeBookId === book.id"
                :disabled="updatingBook && activeBookId === book.id"
                @click="toggleBookCreation(book.id, book.allow_new_nodes)"
              >
                {{ book.allow_new_nodes ? '关闭创作' : '开放创作' }}
              </n-button>

              <n-button
                size="small"
                tertiary
                @click="toggleEditBook(book)"
              >
                {{ expandedBookId === book.id ? '收起编辑' : '编辑详情' }}
              </n-button>

              <n-button
                v-for="phase in phaseOptions"
                :key="phase.value"
                size="small"
                :type="book.phase === phase.value ? 'default' : 'tertiary'"
                :disabled="book.phase === phase.value || (updatingBook && activeBookId === book.id)"
                :loading="updatingBook && activeBookId === book.id && book.phase !== phase.value"
                @click="updateBookPhase(book.id, phase.value)"
              >
                {{ phase.label }}
              </n-button>
            </div>

            <div v-if="expandedBookId === book.id && editState[book.id]" class="admin-book-editor">
              <label class="admin-field">
                <span class="admin-field__label">标题</span>
                <n-input
                  :value="editState[book.id]!.title"
                  @update:value="editState[book.id]!.title = $event"
                />
              </label>

              <label class="admin-field admin-field--wide">
                <span class="admin-field__label">简介</span>
                <n-input
                  :value="editState[book.id]!.description"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 6 }"
                  @update:value="editState[book.id]!.description = $event"
                />
              </label>

              <label class="admin-field admin-field--wide">
                <span class="admin-field__label">封面链接</span>
                <n-input
                  :value="editState[book.id]!.cover_image"
                  @update:value="editState[book.id]!.cover_image = $event"
                />
              </label>

              <label class="admin-field">
                <span class="admin-field__label">阶段</span>
                <n-select
                  :value="editState[book.id]!.phase"
                  :options="phaseOptions"
                  @update:value="editState[book.id]!.phase = $event"
                />
              </label>

              <label class="admin-field admin-field--switch">
                <span class="admin-field__label">允许新节点</span>
                <div class="admin-switch-row">
                  <span class="admin-switch-row__hint">
                    {{ editState[book.id]!.allow_new_nodes ? '允许继续创作' : '暂时关闭创作' }}
                  </span>
                  <n-switch
                    :value="editState[book.id]!.allow_new_nodes"
                    @update:value="editState[book.id]!.allow_new_nodes = $event"
                  />
                </div>
              </label>

              <label class="admin-field">
                <span class="admin-field__label">开始时间</span>
                <n-date-picker
                  :value="editState[book.id]!.start_at"
                  type="datetime"
                  clearable
                  @update:value="editState[book.id]!.start_at = $event"
                />
              </label>

              <label class="admin-field">
                <span class="admin-field__label">写作截止</span>
                <n-date-picker
                  :value="editState[book.id]!.writing_end_at"
                  type="datetime"
                  clearable
                  @update:value="editState[book.id]!.writing_end_at = $event"
                />
              </label>

              <label class="admin-field">
                <span class="admin-field__label">展示截止</span>
                <n-date-picker
                  :value="editState[book.id]!.showcase_end_at"
                  type="datetime"
                  clearable
                  @update:value="editState[book.id]!.showcase_end_at = $event"
                />
              </label>

              <div class="admin-book-editor__actions">
                <n-button
                  type="primary"
                  :loading="updatingBook && activeBookId === book.id"
                  :disabled="updatingBook && activeBookId === book.id"
                  @click="handleSaveBook(book.id)"
                >
                  保存故事册
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
  grid-template-columns: minmax(0, 1.8fr) minmax(260px, 0.9fr);
}

.admin-hero__metrics {
  display: grid;
  gap: 12px;
}

.admin-form-grid {
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

.admin-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.admin-book-list {
  display: grid;
  gap: 16px;
}

.admin-book-card {
  display: grid;
  gap: 16px;
  padding: 18px;
}

.admin-book-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.admin-book-card__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.05rem;
}

.admin-book-card__description {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.admin-book-card__badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.admin-book-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  color: var(--text-faint);
  font-size: 12px;
}

.admin-book-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.admin-book-editor {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid var(--line-faint);
}

.admin-book-editor__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  grid-column: 1 / -1;
}

@media (max-width: 900px) {
  .admin-hero,
  .admin-form-grid,
  .admin-book-editor {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .admin-page {
    padding-inline: 12px;
  }

  .admin-book-card__header {
    flex-direction: column;
  }

  .admin-book-card__badges {
    justify-content: flex-start;
  }
}
</style>
