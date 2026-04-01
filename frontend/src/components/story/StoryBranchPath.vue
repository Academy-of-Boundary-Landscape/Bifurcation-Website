<script setup lang="ts">
import { NAvatar, NButton, NSpace } from 'naive-ui'
import { RouterLink, useRoute } from 'vue-router'
import { computed, ref } from 'vue'
import type { StoryNode } from '@/types/models'

const props = defineProps<{
  path: StoryNode[]
}>()

const route = useRoute()
const currentId = computed(() => Number(route.params.nodeId))

// 点击当前节点时跳转到详情页
function handleCurrentClick() {
  if (props.path.length > 0) {
    const currentPathItem = props.path[props.path.length - 1]
    // 如果是当前节点，不跳转（已经在详情页）
    if (currentPathItem && currentPathItem.id === currentId.value) return
  }
}

// 获取路径中每个节点的标题
function getNodeTitle(node: StoryNode): string {
  return node.branch_name || node.title || `节点${node.id}`
}
</script>

<template>
  <div class="flex items-center flex-wrap gap-2 p-4 bg-#1a1a1a border border-#2a2a2a rounded-lg">
    <span class="text-#666666">当前位置:</span>
    
    <template v-for="(item, index) in path" :key="item.id">
      <!-- 根节点 -->
      <router-link 
        v-if="index === 0 && path.length > 1"
        :to="{ name: 'story-node', params: { nodeId: item.id } }"
        class="inline-flex items-center text-#8b5cf6 hover:underline font-semibold"
      >
        {{ getNodeTitle(item) }}
      </router-link>
      
      <!-- 中间节点 -->
      <router-link 
        v-else-if="index > 0 && index < path.length - 1"
        :to="{ name: 'story-node', params: { nodeId: item.id } }"
        class="inline-flex items-center text-#8b5cf6 hover:underline"
      >
        {{ getNodeTitle(item) }}
      </router-link>
      
      <!-- 当前节点（高亮显示） -->
      <span 
        v-else-if="index === path.length - 1"
        class="inline-flex items-center text-white font-bold"
        @click="handleCurrentClick"
      >
        {{ getNodeTitle(item) }}
      </span>
      
      <!-- 箭头分隔符 -->
      <span 
        v-if="index < path.length - 1" 
        class="text-#666666 mx-2"
      >
        →
      </span>
    </template>
  </div>
</template>
