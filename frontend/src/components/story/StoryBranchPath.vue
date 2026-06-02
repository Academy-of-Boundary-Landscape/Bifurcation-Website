<script setup lang="ts">
import type { StoryNode } from '@/types/models'

defineProps<{
  path: StoryNode[]
}>()

// 获取路径中每个节点的标题
function getNodeTitle(node: StoryNode): string {
  return node.branch_name || node.title || `节点${node.id}`
}
</script>

<template>
  <div class="card-base flex items-center flex-wrap gap-2">
    <span class="text-muted">当前位置:</span>

    <template v-for="(item, index) in path" :key="item.id">
      <!-- 父链节点（可跳转） -->
      <router-link
        v-if="index < path.length - 1"
        :to="{ name: 'story-node', params: { nodeId: item.id } }"
        class="inline-flex items-center text-secondary hover:text-primary hover:underline"
        :class="index === 0 ? 'font-semibold' : ''"
      >
        {{ getNodeTitle(item) }}
      </router-link>

      <!-- 当前节点（锁定高亮） -->
      <span
        v-else
        class="inline-flex items-center text-primary font-bold"
      >
        {{ getNodeTitle(item) }}
      </span>

      <!-- 分隔符 -->
      <span
        v-if="index < path.length - 1"
        class="text-muted mx-1"
      >
        →
      </span>
    </template>
  </div>
</template>
