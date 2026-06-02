<script setup lang="ts">
import { computed } from 'vue'
import { NModal, NButton } from 'naive-ui'
import type { AuthorInfo, NodeStatus } from '@/types/models'
import { storyStatusLabel } from '@/utils/storyStatus'

interface CreationContextNode {
  id: number
  title?: string | null
  branch_name?: string | null
  summary?: string | null
  created_at: string
  status: NodeStatus
  author?: AuthorInfo | null
}

const props = defineProps<{
  show: boolean
  bookTitle?: string | null
  parentNode?: CreationContextNode | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  confirm: []
}>()

const isFirstNode = computed(() => !props.parentNode)
const nodeDisplayTitle = computed(
  () => props.parentNode?.branch_name || props.parentNode?.title || (props.parentNode ? `节点 ${props.parentNode.id}` : ''),
)
const nodeSummary = computed(() => props.parentNode?.summary?.trim() || '当前节点还没有摘要，进入创作页后可以直接阅读正文上下文。')
const createdDate = computed(() => {
  if (!props.parentNode?.created_at) return ''
  return new Date(props.parentNode.created_at).toLocaleDateString('zh-CN')
})

function closeModal() {
  emit('update:show', false)
}

function handleConfirm() {
  emit('confirm')
  closeModal()
}
</script>

<template>
  <n-modal
    :show="show"
    :mask-closable="true"
    :auto-focus="false"
    @update:show="emit('update:show', $event)"
  >
    <div class="story-create-confirm ui-shell-panel ui-shell-panel--raised">
      <div class="story-create-confirm__head">
        <p class="ui-shell-kicker">Creation Confirm</p>
        <h3 class="ui-shell-title story-create-confirm__title">
          {{ isFirstNode ? '创建第一个节点' : '确认创建后续节点' }}
        </h3>
        <p class="story-create-confirm__lead">
          {{
            isFirstNode
              ? `你将为《${bookTitle || '当前故事册'}》写下起始节点，之后整棵故事树都会从这里展开。`
              : '你将基于当前节点继续创作。先确认上下文，再进入完整写作页。'
          }}
        </p>
      </div>

      <div v-if="parentNode" class="story-create-confirm__context ui-panel-section">
        <p class="ui-panel-section__label">当前上下文</p>
        <div class="story-create-confirm__meta">
          <div>
            <p class="story-create-confirm__node-title">{{ nodeDisplayTitle }}</p>
            <p class="story-create-confirm__node-subtitle">
              作者：{{ parentNode.author?.username || '未知作者' }}
              <span v-if="createdDate"> · {{ createdDate }}</span>
            </p>
          </div>
          <span class="ui-chip">{{ storyStatusLabel(parentNode.status) }}</span>
        </div>
        <p class="story-create-confirm__summary">
          {{ nodeSummary }}
        </p>
      </div>

      <div v-else class="story-create-confirm__context ui-panel-section">
        <p class="ui-panel-section__label">起始说明</p>
        <p class="story-create-confirm__summary">
          这是该故事册的第一个节点。建议先写出明确的开场、基础设定和足够清晰的叙事方向，为后续分支留出空间。
        </p>
      </div>

      <div class="story-create-confirm__tips">
        <p>进入写作页后，你会看到更完整的父节点信息、草稿状态和提交说明。</p>
        <p>提交后新节点会进入待审核状态，审核通过后才会向其他读者公开。</p>
      </div>

      <div class="story-create-confirm__actions">
        <n-button @click="closeModal">
          暂不进入
        </n-button>
        <n-button type="primary" @click="handleConfirm">
          进入创作页
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<style scoped>
.story-create-confirm {
  width: min(560px, calc(100vw - 32px));
  margin: 24px auto;
  padding: 24px;
}

.story-create-confirm__head {
  display: grid;
  gap: 10px;
}

.story-create-confirm__title {
  font-size: 1.55rem;
}

.story-create-confirm__lead {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.story-create-confirm__context {
  margin-top: 18px;
  padding: 16px;
}

.story-create-confirm__meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
}

.story-create-confirm__node-title {
  margin: 0;
  font-size: 1.05rem;
  color: var(--text-primary);
}

.story-create-confirm__node-subtitle {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 0.92rem;
}

.story-create-confirm__summary {
  margin: 14px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.story-create-confirm__tips {
  display: grid;
  gap: 8px;
  margin-top: 16px;
  color: var(--text-muted);
  font-size: 0.94rem;
  line-height: 1.75;
}

.story-create-confirm__tips p {
  margin: 0;
}

.story-create-confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 22px;
}

@media (max-width: 640px) {
  .story-create-confirm {
    padding: 18px;
  }

  .story-create-confirm__meta {
    flex-direction: column;
  }

  .story-create-confirm__actions {
    flex-direction: column-reverse;
  }
}
</style>
