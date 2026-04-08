<script setup lang="ts">
import { NCard, NButton, NSpace, NSpin, NAvatar, NInput, NFormItem, NAlert } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref, watch, onBeforeUnmount, onMounted } from 'vue'
import type { StoryNodeCreate } from '@/types/models'
import { useMessage } from 'naive-ui'
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

const draftStatusText = computed(() => {
  if (!hasMeaningfulDraftContent.value) {
    return '尚未生成本地草稿'
  }

  if (draftSaveState.value === 'saving') {
    return '正在保存本地草稿...'
  }

  if (lastSavedAt.value) {
    return `本地草稿已保存于 ${new Date(lastSavedAt.value).toLocaleString('zh-CN')}`
  }

  return '本地草稿已保存'
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
    message.error('内容不能为空')
    return
  }

  if (contentLength.value < 50) {
    message.warning('内容过短，建议至少50字')
  }

  createNode(formData.value, {
    onSuccess: (data) => {
      message.success('创作提交成功，等待审核')
      clearDraft()
      void router.push({ name: 'story-node', params: { nodeId: data.id }, query: { submitted: '1' } })
    },
    onError: (error) => {
      message.error('创作提交失败，请重试')
      console.error('提交失败:', error)
    },
  })
}

function handleDiscardDraft() {
  clearDraft()
  wasRestoredFromDraft.value = false
  resetForm()
  message.success('本地草稿已清除')
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
  <div class="story-write-page">
    <n-spin :show="isParentLoading">
      <n-space vertical :size="24">
        <n-card v-if="parentNode" class="ui-shell-panel" :bordered="false">
          <template #header>
            <h2 class="ui-shell-title">前文摘要</h2>
          </template>

          <div class="story-write-summary">
            <n-avatar :size="32">
              {{ parentNode.author?.username?.charAt(0).toUpperCase() }}
            </n-avatar>
            <div>
              <h3 class="story-write-summary__title">{{ parentNode.title || parentNode.branch_name || '无标题' }}</h3>
              <p class="story-write-muted">作者: {{ parentNode.author?.username }} | {{ new Date(parentNode.created_at).toLocaleDateString('zh-CN') }}</p>
            </div>
          </div>

          <div class="story-write-excerpt">
            {{ parentNode.content.substring(0, 300) }}{{ parentNode.content.length > 300 ? '...' : '' }}
          </div>

          <div class="story-write-footer">
            <RouterLink
              :to="`/story/node/${parentNode.id}`"
              class="story-write-link"
            >
              查看完整前文 →
            </RouterLink>
          </div>
        </n-card>

        <n-card class="ui-shell-panel" :bordered="false">
          <template #header>
            <h2 class="ui-shell-title">创建后续节点</h2>
          </template>

          <div class="space-y-4">
            <n-alert type="info" :bordered="false" class="story-write-draft-status">
              <div class="story-write-draft-status__content">
                <div>
                  <p class="story-write-draft-status__title">本地草稿保护已开启</p>
                  <p class="story-write-draft-status__text">{{ draftStatusText }}</p>
                </div>
                <n-button
                  v-if="hasMeaningfulDraftContent"
                  tertiary
                  size="small"
                  @click="handleDiscardDraft"
                >
                  清除草稿
                </n-button>
              </div>
            </n-alert>

            <n-alert
              v-if="wasRestoredFromDraft"
              type="success"
              :bordered="false"
              class="story-write-draft-status"
            >
              已恢复本地草稿。你可以继续编辑，提交成功后这份草稿会自动清除。
            </n-alert>

            <div class="story-write-muted">
              <p>您正在从「{{ parentNode?.title || parentNode?.branch_name || '该节点' }}」继续创作新的后续节点。</p>
              <p>您可以延续现有走向，也可以写出新的可能性；分支名称现在是可选信息，而不是另一种独立操作。</p>
            </div>

            <div class="story-write-rules">
              <h3 class="story-write-rules__title">创作要求</h3>
              <ul class="story-write-rules__list">
                <li>内容需符合世界观设定</li>
                <li>建议字数：50-2000字</li>
                <li>禁止包含违法不良信息</li>
              </ul>
            </div>
          </div>
        </n-card>

        <n-card class="ui-shell-panel" :bordered="false">
          <template #header>
            <h2 class="ui-shell-title">创作内容</h2>
          </template>

          <div class="space-y-6">
            <n-form-item label="分支名称（可选）">
              <n-input
                v-model:value="formData.branch_name"
                placeholder="例如：平行世界的相遇"
                class="w-full"
              />
            </n-form-item>

            <n-form-item label="标题（可选）">
              <n-input
                v-model:value="formData.title"
                placeholder="为您的创作添加一个标题"
                class="w-full"
              />
            </n-form-item>

            <n-form-item label="正文内容" required>
              <n-input
                v-model:value="formData.content"
                type="textarea"
                placeholder="开始您的创作..."
                :rows="12"
                class="w-full"
              />
              <div class="story-write-counter">
                <span>字数: {{ contentLength }}</span>
                <span v-if="contentLength < 50" class="text-yellow-400">建议至少50字</span>
                <span v-else-if="contentLength > 2000" class="text-red-400">超过2000字</span>
              </div>
            </n-form-item>
          </div>
        </n-card>

        <n-card class="ui-shell-panel" :bordered="false">
          <div class="story-write-actions">
            <div class="story-write-muted">
              <p>您的创作将进入审核流程，通过后即可发布</p>
              <p class="story-write-muted__sub">内容会自动保存到当前浏览器。误刷新或临时离开后，返回这里即可恢复继续创作。</p>
            </div>

            <n-space>
              <n-button @click="handleBack" size="large">
                返回
              </n-button>
              <n-button
                type="primary"
                size="large"
                @click="handleSubmit"
                :loading="isCreating"
                :disabled="isCreating"
              >
                提交后续节点
              </n-button>
            </n-space>
          </div>
        </n-card>
      </n-space>
    </n-spin>
  </div>
</template>

<style scoped>
.story-write-page {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px 16px 40px;
}

.story-write-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.story-write-summary__title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.05rem;
  font-weight: 600;
}

.story-write-muted {
  color: var(--text-muted);
  line-height: 1.75;
}

.story-write-muted__sub {
  margin-top: 2px;
  font-size: 13px;
}

.story-write-excerpt {
  color: var(--text-primary);
  line-height: 1.9;
  white-space: pre-wrap;
}

.story-write-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
}

.story-write-link {
  color: var(--accent-cool);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 12px;
}

.story-write-draft-status {
  background: rgba(255, 255, 255, 0.03);
}

.story-write-draft-status__content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.story-write-draft-status__title {
  margin: 0 0 4px;
  color: var(--text-primary);
  font-size: 0.96rem;
}

.story-write-draft-status__text {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.story-write-rules {
  padding: 16px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.025);
}

.story-write-rules__title {
  margin: 0 0 8px;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
}

.story-write-rules__list {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 6px;
  color: var(--text-muted);
}

.story-write-counter {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.story-write-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (min-width: 640px) {
  .story-write-actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

@media (max-width: 640px) {
  .story-write-draft-status__content {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
