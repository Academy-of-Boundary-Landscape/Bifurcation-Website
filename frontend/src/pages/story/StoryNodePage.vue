<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NAvatar, NInput, NSelect } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import { useAuditStoryNodeMutation } from '@/features/admin/queries'
import { canCreateFromStoryNode, getStoryNodeCreationBlockedReason } from '@/features/story/creation'
import { buildStoryWriteRoute } from '@/features/story/navigation'
import StoryCreateConfirmModal from '@/components/story/StoryCreateConfirmModal.vue'
import StoryBranchPath from '@/components/story/StoryBranchPath.vue'
import { storyStatusLabel } from '@/utils/storyStatus'
import {
  useDeleteStoryNodeMutation,
  useNodeChildrenQuery,
  useNodeDetailQuery,
  useNodePathQuery,
} from '@/features/story/queries'
import {
  useCreateCommentMutation,
  useDeleteCommentMutation,
  useInfiniteNodeCommentsQuery,
  useToggleLikeMutation,
} from '@/features/interaction/queries'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const nodeId = computed(() => Number(route.params.nodeId))
const justSubmitted = computed(() => route.query.submitted === '1')

const { data: node, isLoading } = useNodeDetailQuery(nodeId)
const { data: path } = useNodePathQuery(nodeId)
const { data: children } = useNodeChildrenQuery(nodeId, { limit: 5 })
const {
  data: commentPages,
  isFetchingNextPage: loadingMoreComments,
  hasNextPage: hasMoreComments,
  fetchNextPage: fetchMoreComments,
} = useInfiniteNodeCommentsQuery(nodeId)
// 把所有 page 拍平成一条 flat 列表
const comments = computed(() => commentPages.value?.pages.flat() ?? [])
const loadedCommentsCount = computed(() => comments.value.length)
// 评论总数：优先使用后端 node.comments_count（denormalized 真实总数），
// 在还没拿到时回退到本地已加载量
const totalCommentsCount = computed(() => node.value?.comments_count ?? loadedCommentsCount.value)

const { mutate: toggleLike, isPending: togglingLike } = useToggleLikeMutation()

// 提交评论
const commentContent = ref('')
const { mutate: submitComment, isPending: submittingComment } = useCreateCommentMutation()

// 删除评论
const { mutate: deleteComment, isPending: deletingComment } = useDeleteCommentMutation()
const { mutate: deleteNode, isPending: deletingNode } = useDeleteStoryNodeMutation()
const { mutate: auditNode, isPending: auditingNode } = useAuditStoryNodeMutation()

function handleToggleLike() {
  toggleLike(
    { nodeId: nodeId.value, bookId: node.value?.book_id },
    {
      onSuccess: (data) => {
        message.success(data.action === 'liked' ? '点赞成功' : '已取消点赞')
      },
      onError: () => {
        message.error('操作失败，请重试')
      },
    }
  )
}

function handleSubmitComment() {
  submitComment(
    { nodeId: nodeId.value, payload: { content: commentContent.value } },
    {
      onSuccess: () => {
        message.success('评论成功')
        commentContent.value = ''
      },
      onError: () => {
        message.error('评论失败，请重试')
      },
    }
  )
}

function handleDeleteComment(commentId: number) {
  deleteComment(
    { commentId, nodeId: nodeId.value },
    {
      onSuccess: () => {
        message.success('评论已删除')
      },
      onError: () => {
        message.error('删除失败，请重试')
      },
    }
  )
}

const canCreateChild = computed(() => canCreateFromStoryNode(node.value))
const creationBlockedReason = computed(() => getStoryNodeCreationBlockedReason(node.value))
const isAdmin = computed(() => authStore.currentUser?.role === 'admin')
const adminTargetStatus = ref<'published' | 'archived'>('published')
const adminReason = ref('')
const showCreateModal = ref(false)
const adminStatusOptions = [
  { label: '设为已发布', value: 'published' },
  { label: '设为已归档', value: 'archived' },
]

watch(
  () => node.value?.status,
  (status) => {
    adminTargetStatus.value = status === 'archived' ? 'published' : 'archived'
    adminReason.value = ''
  },
  { immediate: true },
)

function handleCreateChildNode() {
  if (!authStore.isAuthenticated) {
    void router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  showCreateModal.value = true
}

function confirmCreateChildNode() {
  if (!node.value) return
  void router.push(buildStoryWriteRoute(node.value.book_id, nodeId.value))
}

// 处理编辑节点
// 处理删除节点
function handleDelete() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }

  if (!globalThis.confirm('确定要删除这个节点吗？')) {
    return
  }

  deleteNode(
    { nodeId: nodeId.value },
    {
      onSuccess: () => {
        message.success('节点删除成功')
        router.push({ name: 'books' })
      },
      onError: (error) => {
        console.error('删除失败:', error)
        message.error('删除失败，请重试')
      },
    }
  )
}

function handleAdminStatusUpdate() {
  if (!node.value) return

  const payload =
    adminTargetStatus.value === 'archived'
      ? { status: 'archived' as const, reject_reason: adminReason.value.trim() || undefined }
      : { status: 'published' as const }

  auditNode(
    {
      nodeId: nodeId.value,
      payload,
    },
    {
      onSuccess: () => {
        message.success(adminTargetStatus.value === 'published' ? '节点已发布' : '节点已归档')
        if (adminTargetStatus.value === 'archived') {
          adminReason.value = ''
        }
      },
      onError: () => {
        message.error('状态更新失败，请重试')
      },
    },
  )
}
</script>

<template>
  <div class="story-node-page">
    <n-spin :show="isLoading">
      <story-branch-path v-if="path && path.length > 0" :path="path" />

      <n-card v-if="node" class="story-node-panel ui-shell-panel mb-6" :bordered="false">
        <div class="story-node-head">
          <div>
            <p class="ui-shell-kicker">Node Record</p>
            <h1 class="ui-shell-title story-node-title">
              {{ node.title ?? node.branch_name ?? '无标题' }}
            </h1>
            <div class="story-node-meta">
              <n-avatar 
                :size="32" 
                :src="node.author?.avatar ?? undefined"
              >
                {{ node.author?.username?.charAt(0).toUpperCase() ?? '' }}
              </n-avatar>
              <span class="story-node-meta__item">{{ node.author?.username ?? '系统' }}</span>
              <span class="story-node-meta__item">{{ new Date(node.created_at).toLocaleDateString('zh-CN') }}</span>
            </div>
          </div>
          <n-tag :type="node.status === 'published' ? 'success' : 'warning'">
            {{ node.is_ending ? storyStatusLabel('ending') : storyStatusLabel(node.status) }}
          </n-tag>
        </div>

        <div class="story-node-actions">
          <n-button
            size="small"
            @click="router.push({ name: 'book-detail', params: { bookId: node.book_id }, query: { focusNodeId: node.id } })"
          >
            返回故事树
          </n-button>
        </div>

        <div
          v-if="justSubmitted && node.status === 'pending'"
          class="story-node-notice story-node-notice--pending"
        >
          您的投稿已提交成功，当前处于待审核状态。审核通过后，这个节点会对其他读者公开可见。
        </div>

        <div
          v-else-if="node.status === 'pending'"
          class="story-node-notice story-node-notice--pending"
        >
          该节点正在审核中，目前仅作者本人和管理员可见。
        </div>

        <div
          v-else-if="node.status === 'archived'"
          class="story-node-notice story-node-notice--archived"
        >
          <p>该节点已归档，普通读者不可见。</p>
          <p v-if="node.reject_reason || node.archived_reason" class="mt-2">
            原因：{{ node.reject_reason || node.archived_reason }}
          </p>
        </div>

        <div v-if="isAdmin" class="story-node-admin-panel">
          <div class="story-node-admin-toolbar">
            <div class="story-node-admin-toolbar__meta">
              <p class="ui-shell-kicker">Admin</p>
              <div class="story-node-admin-toolbar__status">
                <span class="story-node-admin-toolbar__label">当前状态</span>
                <n-tag size="small" :type="node.status === 'published' ? 'success' : node.status === 'archived' ? 'error' : 'warning'">
                  {{ storyStatusLabel(node.status) }}
                </n-tag>
              </div>
            </div>

            <div class="story-node-admin-toolbar__controls">
              <n-select
                v-model:value="adminTargetStatus"
                size="small"
                class="story-node-admin-toolbar__select"
                :options="adminStatusOptions"
              />
              <n-button
                size="small"
                type="primary"
                :loading="auditingNode"
                :disabled="auditingNode || adminTargetStatus === node.status"
                @click="handleAdminStatusUpdate"
              >
                应用
              </n-button>
            </div>
          </div>

          <div v-if="adminTargetStatus === 'archived'" class="story-node-admin-toolbar__reason">
            <n-input
              v-model:value="adminReason"
              size="small"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 3 }"
              placeholder="归档原因，可选"
            />
          </div>
        </div>
        
        <n-space class="story-node-actions">
          <!-- 已点赞用 primary（白底）+ 实心心型；未点赞用 secondary 描边 + 空心心型 -->
          <n-button
            :type="node.is_liked ? 'primary' : 'default'"
            :secondary="!node.is_liked"
            class="story-node-like-btn"
            :class="{ 'story-node-like-btn--liked': node.is_liked }"
            @click="handleToggleLike"
            :loading="togglingLike && node?.id === nodeId"
          >
            <span class="story-node-like-btn__icon" aria-hidden="true">
              {{ node.is_liked ? '♥' : '♡' }}
            </span>
            {{ node.likes_count ?? 0 }} {{ node.is_liked ? '已赞' : '点赞' }}
          </n-button>
          <n-button @click="handleCreateChildNode" :disabled="!canCreateChild">
            创建后续节点
          </n-button>
          
          <!-- 编辑和删除按钮（仅作者可见） -->
          <n-button 
            v-if="authStore.currentUser?.id === node.author?.id" 
            type="error" 
            @click="handleDelete"
          >
            ❌ 删除
          </n-button>
        </n-space>

        <p v-if="creationBlockedReason" class="story-node-muted">
          {{ creationBlockedReason }}
        </p>
      </n-card>

      <n-card v-if="node?.content" class="story-node-reading ui-shell-panel mb-6" :bordered="false">
        <div class="story-node-reading__body">
          {{ node.content }}
        </div>
      </n-card>

      <n-card v-if="children && children.length > 0" class="ui-shell-panel" :bordered="false">
        <template #header>
          <h2 class="ui-shell-title story-node-section-title">子分支（{{ children.length }}）</h2>
        </template>
        
        <div class="space-y-4">
          <div 
            v-for="child in children" 
            :key="child.id" 
            class="story-node-child"
            @click="$router.push({ name: 'story-node', params: { nodeId: child.id } })"
          >
            <div class="flex items-center gap-3">
              <n-avatar 
                :size="32" 
                :src="child.author?.avatar ?? undefined"
              >
                {{ child.author?.username?.charAt(0).toUpperCase() }}
              </n-avatar>
              <div class="flex-1 min-w-0">
                <h3 class="story-node-child__title">{{ child.title || child.branch_name || '无标题' }}</h3>
                <p class="story-node-child__summary">
                  {{ child.summary || '这个分支还没有补充摘要，点击查看正文。' }}
                </p>
                <div class="story-node-child__meta">
                  <span class="story-node-child__meta-item">{{ new Date(child.created_at).toLocaleDateString('zh-CN') }}</span>
                  <span class="story-node-child__meta-item">{{ storyStatusLabel(child.status) }}</span>
                  <span class="story-node-child__meta-item">{{ child.likes_count }} 赞</span>
                  <span class="story-node-child__meta-item">{{ child.comments_count }} 评论</span>
                  <span class="story-node-child__meta-item">{{ child.children_count }} 分支</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-card>
      
      <n-card v-if="node && (!children || children.length === 0)" class="ui-shell-panel" :bordered="false">
        <template #header>
          <h2 class="ui-shell-title story-node-section-title">子分支（{{ children?.length || 0 }}）</h2>
        </template>
        
        <div class="story-node-empty">
          <p class="story-node-muted">暂无子分支，成为第一个创建者。</p>
          
          <div class="mt-4">
            <n-button 
              type="primary" 
              size="large" 
              @click="handleCreateChildNode"
            >
              开始创建后续节点
            </n-button>
          </div>
        </div>
      </n-card>
      
      <n-card class="ui-shell-panel" :bordered="false">
        <template #header>
          <h2 class="ui-shell-title story-node-section-title">
            评论区（{{ totalCommentsCount }}<template v-if="loadedCommentsCount < totalCommentsCount">·已显示 {{ loadedCommentsCount }}</template>）
          </h2>
        </template>
        
        <div v-if="authStore.isAuthenticated" class="story-node-comment-form">
          <textarea 
            v-model="commentContent" 
            class="story-node-comment-input"
            placeholder="写下您的评论..."
          ></textarea>
          <div class="mt-4">
            <n-button 
              type="primary" 
              @click="handleSubmitComment"
              :loading="submittingComment"
              :disabled="!commentContent.trim() || submittingComment"
            >
              发表评论
            </n-button>
          </div>
        </div>
        
        <div v-else class="story-node-muted">
          请登录后发表评论
        </div>
        
        <div v-if="comments && comments.length > 0" class="space-y-4">
          <div 
            v-for="comment in comments" 
            :key="comment.id" 
            class="story-node-comment"
          >
            <n-avatar 
              :size="24" 
              :src="comment.user?.avatar ?? undefined"
              class="mt-1"
            >
              {{ comment.user?.username?.charAt(0).toUpperCase() }}
            </n-avatar>
            <div class="flex-1 min-w-0">
              <div class="story-node-comment__meta">
                <span class="story-node-comment__author">{{ comment.user?.username }}</span>
                <span class="story-node-comment__time">{{ new Date(comment.created_at).toLocaleDateString('zh-CN') }}</span>
                <n-button 
                  v-if="authStore.currentUser?.id === comment.user?.id" 
                  size="small" 
                  type="error" 
                  @click="handleDeleteComment(comment.id)"
                  :loading="deletingComment && comments.find(c => c.id === comment.id)?.id === comment.id"
                  :disabled="deletingComment && comments.find(c => c.id === comment.id)?.id === comment.id"
                >
                  删除
                </n-button>
              </div>
              
              <p class="story-node-comment__content">{{ comment.content }}</p>
            </div>
          </div>

          <!-- 加载更多 -->
          <div v-if="hasMoreComments" class="story-node-comments-more">
            <n-button
              quaternary
              size="medium"
              :loading="loadingMoreComments"
              @click="() => void fetchMoreComments()"
            >
              加载更多
              <template v-if="totalCommentsCount > loadedCommentsCount">
                （还剩 {{ Math.max(0, totalCommentsCount - loadedCommentsCount) }} 条）
              </template>
            </n-button>
          </div>
          <div v-else-if="loadedCommentsCount > 0" class="story-node-comments-end">
            <span aria-hidden="true">·</span>
            已加载全部 {{ totalCommentsCount }} 条
            <span aria-hidden="true">·</span>
          </div>
        </div>

        <div v-else class="story-node-empty">
          <p class="story-node-muted">暂无评论</p>
          
          <div class="mt-4">
            <n-button 
              v-if="authStore.isAuthenticated" 
              type="primary" 
              size="large" 
              disabled
              >
                成为第一个评论者
              </n-button>
          </div>
        </div>
      </n-card>

      <story-create-confirm-modal
        v-if="node"
        v-model:show="showCreateModal"
        :book-title="null"
        :parent-node="node"
        @confirm="confirmCreateChildNode"
      />
    </n-spin>
  </div>
</template>

<style scoped>
.story-node-page {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px 16px 40px;
}

.story-node-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.story-node-section-title {
  margin: 8px 0 0;
  letter-spacing: 0.05em;
}

.story-node-title {
  margin-top: 6px;
  font-size: clamp(1.8rem, 4vw, 2.8rem);
}

.story-node-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  color: var(--text-muted);
}

.story-node-meta__item {
  letter-spacing: 0.04em;
}

.story-node-actions {
  margin-bottom: 16px;
}

/* 点赞按钮 */
.story-node-like-btn__icon {
  display: inline-block;
  margin-right: 4px;
  font-size: 1.1em;
  line-height: 1;
  transition: transform 220ms ease;
}

.story-node-like-btn:hover .story-node-like-btn__icon {
  transform: scale(1.15);
}

/* 已点赞态：实心心型 + 白底 + 黑字（用现有 primary 颜色，覆盖 type 即可） */
.story-node-like-btn--liked .story-node-like-btn__icon {
  color: var(--state-danger);
}

.story-node-notice {
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  font-size: 14px;
  line-height: 1.75;
}

.story-node-notice--pending {
  background: rgba(215, 201, 134, 0.08);
  color: #ebe2b3;
  border-color: rgba(215, 201, 134, 0.28);
}

.story-node-notice--archived {
  background: rgba(210, 143, 143, 0.08);
  color: #efcccc;
  border-color: rgba(210, 143, 143, 0.28);
}

.story-node-admin-panel {
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.025);
}

.story-node-admin-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.story-node-admin-toolbar__meta {
  display: grid;
  gap: 8px;
}

.story-node-admin-toolbar__status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.story-node-admin-toolbar__label {
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.story-node-admin-toolbar__controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.story-node-admin-toolbar__select {
  width: 140px;
}

.story-node-admin-toolbar__reason {
  margin-top: 10px;
}

@media (max-width: 720px) {
  .story-node-admin-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .story-node-admin-toolbar__controls {
    width: 100%;
  }

  .story-node-admin-toolbar__select {
    flex: 1;
    width: auto;
  }
}

.story-node-reading__body {
  color: var(--text-primary);
  white-space: pre-wrap;
  line-height: 2;
  font-size: 16px;
}

.story-node-child__title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
}

.story-node-child {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line-faint);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.story-node-child:last-child {
  border-bottom: none;
}

.story-node-child:hover {
  background: rgba(255, 255, 255, 0.02);
}

.story-node-child__summary {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
}

.story-node-child__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.story-node-child__meta-item {
  white-space: nowrap;
}

.story-node-empty {
  padding: 48px 16px;
  text-align: center;
}

.story-node-comments-more {
  display: flex;
  justify-content: center;
  padding-top: 16px;
}

.story-node-comments-end {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding-top: 20px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.story-node-muted {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.75;
}

.story-node-comment-form {
  margin-bottom: 24px;
}

.story-node-comment-input {
  width: 100%;
  min-height: 112px;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.025);
  color: var(--text-primary);
  outline: none;
  resize: vertical;
}

.story-node-comment-input:focus {
  border-color: var(--line-strong);
  box-shadow: var(--glow-focus);
}

.story-node-comment {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line-faint);
}

.story-node-comment:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.story-node-comment__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.story-node-comment__author {
  color: var(--text-primary);
  font-weight: 600;
}

.story-node-comment__time {
  color: var(--text-muted);
  font-size: 12px;
}

.story-node-comment__content {
  margin-top: 8px;
  color: var(--text-primary);
  white-space: pre-wrap;
  line-height: 1.8;
}
</style>
