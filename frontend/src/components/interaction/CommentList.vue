<script setup lang="ts">
import { NCard, NAvatar, NButton, NSpin } from 'naive-ui'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDeleteCommentMutation, useInfiniteNodeCommentsQuery } from '@/features/interaction/queries'

const props = defineProps<{
  nodeId: number
  /** 来自 node.comments_count，作为评论"总数"显示。
   *  必传——不传时用本地已加载量代替（不准确）。 */
  commentsCount?: number
}>()

const authStore = useAuthStore()

const {
  data: commentPages,
  isLoading,
  isFetchingNextPage,
  hasNextPage,
  fetchNextPage,
  refetch,
} = useInfiniteNodeCommentsQuery(computed(() => props.nodeId))

const { mutate: deleteComment } = useDeleteCommentMutation()

// 把所有 page 拍平成一条 flat 列表
const comments = computed(() => commentPages.value?.pages.flat() ?? [])
const loadedCount = computed(() => comments.value.length)

// 总数显示：优先用父级传的 commentsCount（来自 node.comments_count），
// 否则回退到已加载的本地长度
const displayTotal = computed(() => props.commentsCount ?? loadedCount.value)
const hasMore = computed(() => Boolean(hasNextPage.value))

function handleRefresh() {
  void refetch()
}

function handleLoadMore() {
  void fetchNextPage()
}

function handleDeleteComment(commentId: number) {
  deleteComment({ commentId, nodeId: props.nodeId })
}
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-bold text-white">
          评论区
          <span class="text-#666666 text-sm font-normal ml-2">
            <template v-if="commentsCount !== undefined && loadedCount < commentsCount">
              已显示 {{ loadedCount }} / {{ commentsCount }}
            </template>
            <template v-else>
              {{ displayTotal }}
            </template>
          </span>
        </h3>
        <n-button size="small" @click="handleRefresh" v-if="!isLoading">刷新</n-button>
      </div>
    </template>

    <div v-if="isLoading" class="text-center py-8">
      <p class="text-#666666">加载中...</p>
    </div>

    <div v-else-if="comments.length === 0" class="text-center py-8">
      <p class="text-#666666">暂无评论，快来发表第一条评论吧！</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="border-b border-#2a2a2a pb-4 last:border-b-0 last:pb-0"
      >
        <div class="flex items-start gap-3">
          <n-avatar :size="32">
            {{ comment.user?.username?.charAt(0).toUpperCase() }}
          </n-avatar>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium text-white">{{ comment.user?.username }}</span>
              <span class="text-#666666 text-sm">{{ new Date(comment.created_at).toLocaleString('zh-CN') }}</span>
            </div>
            <p class="text-#d9d9d9">{{ comment.content }}</p>
          </div>
          <div v-if="authStore.isAuthenticated && comment.user?.id === authStore.currentUser?.id" class="flex flex-col items-end">
            <n-button size="small" @click="handleDeleteComment(comment.id)">删除</n-button>
          </div>
        </div>
      </div>

      <!-- 加载更多 / 已全部加载 -->
      <div v-if="hasMore" class="comment-list__more">
        <n-button
          quaternary
          size="medium"
          :loading="isFetchingNextPage"
          @click="handleLoadMore"
        >
          加载更多
          <template v-if="commentsCount !== undefined">
            （还剩 {{ Math.max(0, commentsCount - loadedCount) }} 条）
          </template>
        </n-button>
      </div>
      <div
        v-else-if="comments.length > 0"
        class="comment-list__end"
      >
        <span class="comment-list__end-mark" aria-hidden="true">·</span>
        已加载全部 {{ displayTotal }} 条
        <span class="comment-list__end-mark" aria-hidden="true">·</span>
      </div>
    </div>
  </n-card>
</template>

<style scoped>
.comment-list__more {
  display: flex;
  justify-content: center;
  padding-top: 12px;
}

.comment-list__end {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding-top: 16px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.comment-list__end-mark {
  color: var(--text-faint);
  opacity: 0.6;
}
</style>
