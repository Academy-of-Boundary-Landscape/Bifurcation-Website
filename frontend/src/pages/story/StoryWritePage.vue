<script setup lang="ts">
import { NButton, NInput, NSpin, useMessage } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, watch, onBeforeUnmount, onMounted } from 'vue'
import type { StoryNodeCreate } from '@/types/models'
import { useCreateStoryNodeMutation, useNodeDetailQuery } from '@/features/story/queries'
import { getStorage, removeStorage, setStorage } from '@/utils/storage'

interface StoryDraftRecord {
  version: 1
  savedAt: string
  data: StoryNodeCreate
}

type DraftSaveState = 'idle' | 'saving' | 'saved'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const bookId = computed(() => Number(route.params.bookId))
const parentId = computed(() => {
  const rawValue = route.query.parentId
  const normalizedValue = Array.isArray(rawValue) ? rawValue[0] : rawValue
  const parsedValue = typeof normalizedValue === 'string' ? Number(normalizedValue) : Number(normalizedValue)
  return Number.isFinite(parsedValue) && parsedValue > 0 ? parsedValue : null
})
const parentNodeQueryId = computed(() => parentId.value ?? 0)

const hasHydratedDraft = ref(false)
const wasRestoredFromDraft = ref(false)
const draftSaveState = ref<DraftSaveState>('idle')
const lastSavedAt = ref<string | null>(null)
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null

function getDraftKey() {
  return `story_node_draft:${bookId.value}:parent:${parentId.value ?? 'root'}`
}

const { data: parentNode, isLoading: isParentLoading } = useNodeDetailQuery(parentNodeQueryId)

const formData = ref<StoryNodeCreate>({
  book_id: bookId.value,
  parent_id: parentId.value ?? undefined,
  title: '',
  content: '',
  branch_name: '',
  zone: 'short',
})

const contentLength = computed(() => formData.value.content.length)
const hasMeaningfulDraftContent = computed(() =>
  Boolean(
    formData.value.content.trim()
    || formData.value.title?.trim()
    || formData.value.branch_name?.trim()
    || formData.value.summary?.trim(),
  ),
)

/* —— 字数状态：50 ~ 2000 是建议区间 —— */
type LengthTone = 'idle' | 'low' | 'ok' | 'high'
const lengthTone = computed<LengthTone>(() => {
  if (contentLength.value === 0) return 'idle'
  if (contentLength.value < 50) return 'low'
  if (contentLength.value > 2000) return 'high'
  return 'ok'
})
const lengthHint = computed(() => {
  switch (lengthTone.value) {
    case 'idle':
      return '建议 50~2000 字'
    case 'low':
      return '建议至少 50 字'
    case 'high':
      return '已超过建议上限 2000 字'
    default:
      return '区间良好'
  }
})

/* —— 草稿状态文字 —— */
const draftStatusText = computed(() => {
  if (!hasMeaningfulDraftContent.value) return '尚无草稿'
  if (draftSaveState.value === 'saving') return '草稿保存中…'
  if (lastSavedAt.value) {
    const diffSec = Math.max(0, Math.floor((Date.now() - new Date(lastSavedAt.value).getTime()) / 1000))
    if (diffSec < 5) return '草稿已保存'
    if (diffSec < 60) return `草稿保存于 ${diffSec} 秒前`
    if (diffSec < 3600) return `草稿保存于 ${Math.floor(diffSec / 60)} 分钟前`
    return `草稿保存于 ${new Date(lastSavedAt.value).toLocaleString('zh-CN')}`
  }
  return '草稿已保存'
})

/* —— 顶部 strip 元数据 —— */
const todayStamp = (() => {
  const d = new Date()
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
})()

const parentMeta = computed(() => {
  if (!parentNode.value) return null
  return {
    id: parentNode.value.id,
    author: parentNode.value.author?.username ?? 'unknown',
    title: parentNode.value.branch_name || parentNode.value.title || '',
    date: parentNode.value.created_at
      ? new Date(parentNode.value.created_at).toLocaleDateString('zh-CN')
      : '',
  }
})

function buildDraftRecord(): StoryDraftRecord {
  return {
    version: 1,
    savedAt: new Date().toISOString(),
    data: {
      ...formData.value,
      book_id: bookId.value,
      parent_id: parentId.value ?? undefined,
    },
  }
}

function clearAutoSaveTimer() {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
    autoSaveTimer = null
  }
}

function clearDraft() {
  removeStorage(getDraftKey())
  lastSavedAt.value = null
  draftSaveState.value = 'idle'
}

function saveDraftImmediately() {
  if (!hasMeaningfulDraftContent.value) {
    clearDraft()
    return
  }
  const draftRecord = buildDraftRecord()
  draftSaveState.value = 'saving'
  setStorage(getDraftKey(), draftRecord)
  draftSaveState.value = 'saved'
  lastSavedAt.value = draftRecord.savedAt
}

function scheduleDraftSave() {
  clearAutoSaveTimer()
  autoSaveTimer = setTimeout(() => {
    saveDraftImmediately()
    autoSaveTimer = null
  }, 900)
}

function restoreDraft() {
  const savedDraft = getStorage<StoryDraftRecord>(getDraftKey())
  if (!savedDraft?.data) return
  formData.value = {
    ...formData.value,
    ...savedDraft.data,
    book_id: bookId.value,
    parent_id: parentId.value ?? undefined,
  }
  lastSavedAt.value = savedDraft.savedAt
  draftSaveState.value = 'saved'
  wasRestoredFromDraft.value = true
}

function loadDraft() {
  const savedDraft = getStorage<StoryDraftRecord>(getDraftKey())
  if (!savedDraft?.data) {
    hasHydratedDraft.value = true
    return
  }

  const shouldRestore = globalThis.confirm(
    `检测到这段创作的本地草稿（保存于 ${new Date(savedDraft.savedAt).toLocaleString('zh-CN')}），是否恢复？`,
  )

  if (shouldRestore) {
    restoreDraft()
  } else {
    clearDraft()
  }

  hasHydratedDraft.value = true
}

function resetForm() {
  formData.value = {
    book_id: bookId.value,
    parent_id: parentId.value ?? undefined,
    title: '',
    content: '',
    branch_name: '',
    zone: 'short',
  }
}

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (!hasMeaningfulDraftContent.value) return
  saveDraftImmediately()
  event.preventDefault()
  event.returnValue = ''
}

onMounted(() => {
  loadDraft()
  window.addEventListener('beforeunload', handleBeforeUnload)
})

watch(
  () => [bookId.value, parentId.value],
  () => {
    formData.value.book_id = bookId.value
    formData.value.parent_id = parentId.value ?? undefined
  },
)

watch(
  formData,
  () => {
    if (!hasHydratedDraft.value) return
    scheduleDraftSave()
  },
  { deep: true },
)

const { mutate: createNode, isPending: isCreating } = useCreateStoryNodeMutation()

function handleBack() {
  saveDraftImmediately()
  void router.back()
}

function handleSubmit() {
  if (!formData.value.content.trim()) {
    message.error('正文不能为空')
    return
  }
  if (contentLength.value < 50) {
    message.warning('内容过短，建议至少 50 字')
  }

  createNode(formData.value, {
    onSuccess: (data) => {
      message.success('提交成功，进入审核流程')
      clearDraft()
      void router.push({ name: 'story-node', params: { nodeId: data.id }, query: { submitted: '1' } })
    },
    onError: (error) => {
      message.error('提交失败，请重试')
      console.error('提交失败:', error)
    },
  })
}

function handleDiscardDraft() {
  clearDraft()
  wasRestoredFromDraft.value = false
  resetForm()
  message.success('草稿已清除')
}

onBeforeUnmount(() => {
  clearAutoSaveTimer()
  if (hasMeaningfulDraftContent.value) {
    saveDraftImmediately()
  }
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<template>
  <div class="write">
    <!-- ============ 顶部 sticky 工作条 ============ -->
    <header class="write__strip">
      <div class="write__strip-left">
        <span class="write__strip-cell">§WRITE</span>
        <span v-if="parentId" class="write__strip-cell">续写自 NODE-{{ parentId }}</span>
        <span v-else class="write__strip-cell">主干起点</span>
        <span v-if="parentMeta?.author" class="write__strip-cell write__strip-cell--soft">@{{ parentMeta.author }}</span>
        <span class="write__strip-cell write__strip-cell--soft">{{ todayStamp }}</span>
      </div>

      <div class="write__strip-right">
        <span class="write__draft-status" :data-state="draftSaveState">
          <span class="write__draft-dot" aria-hidden="true" />
          {{ draftStatusText }}
        </span>
        <button
          v-if="hasMeaningfulDraftContent"
          type="button"
          class="write__strip-link"
          @click="handleDiscardDraft"
        >
          清除草稿
        </button>
        <n-button class="write__strip-back" @click="handleBack" size="medium">
          返回
        </n-button>
        <n-button
          class="write__strip-submit"
          type="primary"
          size="medium"
          :loading="isCreating"
          :disabled="isCreating || !formData.content.trim()"
          @click="handleSubmit"
        >
          提交后续节点 →
        </n-button>
      </div>
    </header>

    <!-- ============ 双栏工作区 ============ -->
    <n-spin :show="isParentLoading" class="write__spin">
      <div class="write__grid">
        <!-- ── 左栏：parent 完整正文 ── -->
        <aside class="write__read" aria-label="上文（parent 正文）">
          <div class="write__read-head">
            <p class="write__col-kicker">PARENT · 上文</p>
            <h2 class="write__read-title">
              {{ parentMeta?.title || (parentId ? '未命名节点' : '这本书的第一个节点') }}
            </h2>
            <p v-if="parentMeta" class="write__read-meta">
              <span>NODE-{{ parentMeta.id }}</span>
              <span v-if="parentMeta.author">@{{ parentMeta.author }}</span>
              <span v-if="parentMeta.date">{{ parentMeta.date }}</span>
            </p>
            <p v-else class="write__read-meta">
              <span>ROOT</span>
              <span>BOOK-{{ bookId }}</span>
            </p>
          </div>

          <div class="write__read-body">
            <div v-if="parentNode" class="write__read-content">{{ parentNode.content }}</div>
            <p v-else-if="!parentId" class="write__read-empty">
              这是这本书的第一个节点。你写下的内容将成为整棵故事树的根，从此往后所有分支都从这里生长。
            </p>
            <p v-else class="write__read-empty">
              正在加载上文……
            </p>
          </div>
        </aside>

        <!-- ── 右栏：写作表单 ── -->
        <section class="write__form" aria-label="续写表单">
          <p class="write__col-kicker">YOUR ENTRY · 续写</p>

          <div v-if="wasRestoredFromDraft" class="write__notice">
            已恢复本地草稿。继续编辑，提交后会自动清除。
          </div>

          <label class="write__field">
            <span class="write__field-label">分支名（可选）</span>
            <n-input
              v-model:value="formData.branch_name"
              placeholder="例如：平行世界的相遇"
              class="write__input"
              :maxlength="60"
              show-count
            />
          </label>

          <label class="write__field">
            <span class="write__field-label">标题（可选）</span>
            <n-input
              v-model:value="formData.title"
              placeholder="为这一节起个名字"
              class="write__input"
              :maxlength="80"
              show-count
            />
          </label>

          <label class="write__field write__field--grow">
            <span class="write__field-label">
              <span>正文</span>
              <span class="write__field-required">必填</span>
            </span>
            <n-input
              v-model:value="formData.content"
              type="textarea"
              placeholder="开始你的续写……"
              class="write__textarea"
              :autosize="{ minRows: 14 }"
            />
            <div class="write__counter" :data-tone="lengthTone">
              <span class="write__counter-num">{{ contentLength }}</span>
              <span class="write__counter-sep">/</span>
              <span class="write__counter-hint">{{ lengthHint }}</span>
            </div>
          </label>

          <p class="write__footnote">
            提交后会进入审核（status: PEND），管理员通过后正式入档（PUB）。
            内容自动保存到当前浏览器，刷新或临时离开都不会丢。
          </p>
        </section>
      </div>
    </n-spin>
  </div>
</template>

<style scoped>
/* ─────────────────────────────────────────────
   外层
   ───────────────────────────────────────────── */
.write {
  min-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

.write__spin {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.write__spin :deep(.n-spin-content) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* ─────────────────────────────────────────────
   顶部 sticky 工作条
   ───────────────────────────────────────────── */
.write__strip {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px 20px;
  padding: 14px clamp(20px, 4vw, 48px);
  background: var(--bg-canvas);
  border-bottom: 1px solid var(--line-soft);
  backdrop-filter: blur(8px);
}

.write__strip-left,
.write__strip-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.write__strip-cell--soft {
  color: var(--text-faint);
}

.write__draft-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.write__draft-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-faint);
  transition: background var(--transition-base);
}

.write__draft-status[data-state="saving"] .write__draft-dot {
  background: var(--state-warning);
  animation: write-pulse 1.4s ease-in-out infinite;
}

.write__draft-status[data-state="saved"] .write__draft-dot {
  background: var(--state-success);
}

.write__strip-link {
  background: none;
  border: 0;
  padding: 0;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
  cursor: pointer;
  transition: color var(--transition-base);
}

.write__strip-link:hover {
  color: var(--state-danger);
}

.write__strip-back {
  --n-color: transparent !important;
  --n-color-hover: var(--bg-panel) !important;
  --n-text-color: var(--text-secondary) !important;
  --n-text-color-hover: var(--text-primary) !important;
  --n-border: 1px solid var(--line-soft) !important;
  --n-border-hover: 1px solid var(--line-strong) !important;
  font-family: var(--font-body) !important;
  font-weight: 400 !important;
  letter-spacing: 0.04em !important;
  border-radius: 2px !important;
}

.write__strip-submit {
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
  border-radius: 2px !important;
}

/* ─────────────────────────────────────────────
   双栏布局
   ───────────────────────────────────────────── */
.write__grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  min-height: 0;
}

@media (min-width: 1024px) {
  .write__grid {
    grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  }
}

/* 共用：列内通用 kicker */
.write__col-kicker {
  margin: 0 0 18px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--text-faint);
}

/* ─────────────────────────────────────────────
   左栏：上文阅读
   ───────────────────────────────────────────── */
.write__read {
  position: relative;
  padding: clamp(28px, 4vw, 56px) clamp(24px, 4vw, 48px);
  border-bottom: 1px solid var(--line-faint);
  background: var(--bg-canvas);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

@media (min-width: 1024px) {
  .write__read {
    border-bottom: 0;
    border-right: 1px solid var(--line-faint);
    /* 让左栏在 viewport 内独立滚动 */
    position: sticky;
    top: 64px;
    height: calc(100vh - 64px - 80px);
    overflow-y: auto;
    scrollbar-width: thin;
  }
}

.write__read-head {
  margin-bottom: clamp(20px, 3vw, 32px);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line-faint);
}

.write__read-title {
  margin: 0 0 12px;
  font-family: var(--font-display);
  font-weight: 500;
  font-size: clamp(1.4rem, 2.6vw, 1.9rem);
  line-height: 1.18;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.write__read-meta {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.write__read-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.write__read-content {
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.95;
  color: var(--text-primary);
  white-space: pre-wrap;
  /* 左栏正文最大宽度，避免阅读时太宽 */
  max-width: 60ch;
}

.write__read-empty {
  margin: 0;
  font-family: var(--font-body);
  font-size: 0.95rem;
  line-height: 1.8;
  color: var(--text-muted);
  max-width: 50ch;
}

/* ─────────────────────────────────────────────
   右栏：续写表单
   ───────────────────────────────────────────── */
.write__form {
  padding: clamp(28px, 4vw, 56px) clamp(24px, 4vw, 48px);
  background: var(--bg-shell);
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 0;
}

.write__notice {
  padding: 10px 14px;
  border-left: 2px solid var(--text-primary);
  background: var(--bg-panel);
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}

.write__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.write__field--grow {
  flex: 1;
  min-height: 0;
}

.write__field-label {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.write__field-required {
  color: var(--text-secondary);
}

.write__input :deep(.n-input__input-el),
.write__input :deep(.n-input__placeholder) {
  font-family: var(--font-body) !important;
  font-size: 0.96rem !important;
}

.write__textarea {
  flex: 1;
}

.write__textarea :deep(.n-input__textarea-el),
.write__textarea :deep(.n-input__placeholder) {
  font-family: var(--font-body) !important;
  font-size: 1rem !important;
  line-height: 1.85 !important;
}

.write__counter {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 4px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.write__counter-num {
  font-size: 0.92rem;
  color: var(--text-primary);
  font-feature-settings: "tnum" 1;
}

.write__counter-sep {
  color: var(--text-faint);
}

.write__counter-hint {
  color: var(--text-muted);
}

.write__counter[data-tone="low"] .write__counter-num,
.write__counter[data-tone="low"] .write__counter-hint {
  color: var(--state-warning);
}

.write__counter[data-tone="high"] .write__counter-num,
.write__counter[data-tone="high"] .write__counter-hint {
  color: var(--state-danger);
}

.write__counter[data-tone="ok"] .write__counter-hint {
  color: var(--state-success);
}

.write__footnote {
  margin: 4px 0 0;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  line-height: 1.7;
  color: var(--text-faint);
  max-width: 60ch;
}

/* ─────────────────────────────────────────────
   动画
   ───────────────────────────────────────────── */
@keyframes write-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.4; }
}

@media (prefers-reduced-motion: reduce) {
  .write__draft-dot,
  .write__strip-back,
  .write__strip-submit {
    transition: none !important;
    animation: none !important;
  }
}
</style>
