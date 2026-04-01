<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NIcon, NTree } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import type { StoryNodeTreeItem } from '@/types/models'

const props = defineProps<{
  tree: StoryNodeTreeItem[]
}>()

const expandedKeys = ref<string[]>([])

// 格式化节点标题
function getNodeTitle(node: StoryNodeTreeItem): string {
  return node.branch_name || node.title || `节点${node.id}`
}

// 格式化节点内容
function getNodeContent(node: StoryNodeTreeItem): string {
  return node.summary || ''
}

// 格式化节点状态
function getNodeStatus(node: StoryNodeTreeItem): string {
  if (node.is_ending) return '已完结'
  if (node.status === 'pending') return '待审核'
  if (node.status === 'published') return '已发布'
  return '已归档'
}

// 树节点数据转换
function convertToTreeData(items: StoryNodeTreeItem[]): any[] {
  return items.map(item => ({
    key: item.id.toString(),
    label: getNodeTitle(item),
    children: item.children && item.children.length > 0 ? convertToTreeData(item.children) : undefined,
    data: item,
    isLeaf: !item.children || item.children.length === 0,
  }))
}

// 初始化展开状态（默认展开第一层）
onMounted(() => {
  if (props.tree && props.tree.length > 0) {
    const firstLevelKeys = props.tree.map(node => node.id.toString())
    expandedKeys.value = firstLevelKeys
  }
})
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-bold text-white">故事树</h2>
        <n-space>
          <n-button size="small" @click="expandedKeys = []">
            全部收起
          </n-button>
          <n-button size="small" @click="() => expandedKeys = tree.map(n => n.id.toString())">
            全部展开
          </n-button>
        </n-space>
      </div>
    </template>
    
    <n-spin :show="!tree || tree.length === 0">
      <div v-if="!tree || tree.length === 0" class="text-center py-10 text-#666666">
        暂无节点，成为第一个创作者吧！
      </div>
      
      <n-tree 
        v-else 
        :data="convertToTreeData(tree)" 
        block-node 
        :default-expanded-keys="expandedKeys"
        @update:expanded-keys="expandedKeys = $event"
        style="max-height: 600px; overflow-y: auto;"
      >
        <template #default="{ node }">
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <n-icon v-if="node.isLeaf" class="text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <circle cx="12" cy="12" r="6"></circle>
                  <circle cx="12" cy="12" r="2"></circle>
                </svg>
              </n-icon>
              <n-icon v-else class="text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6,12 10,16 18,8"></polyline>
                </svg>
              </n-icon>
              
              <div class="flex-1 min-w-0">
                <div class="font-medium text-white truncate">
                  {{ node.label }}
                </div>
                <div class="text-xs text-#666666 truncate">
                  {{ getNodeContent(node.data as StoryNodeTreeItem) }}
                </div>
              </div>
              
              <div class="flex items-center gap-2 ml-2">
                <n-tag 
                  v-if="(node.data as StoryNodeTreeItem).is_ending" 
                  type="success" 
                  size="small"
                >
                  ✅ 已完结
                </n-tag>
                <n-tag 
                  v-else 
                  :type="(node.data as StoryNodeTreeItem).status === 'published' ? 'success' : 'warning'"
                  size="small"
                >
                  {{ getNodeStatus(node.data as StoryNodeTreeItem) }}
                </n-tag>
                <span class="text-xs text-#666666">{{ (node.data as StoryNodeTreeItem).likes_count }} 赞</span>
              </div>
            </div>
            
            <div class="flex items-center gap-2 ml-4">
              <n-button 
                :component="RouterLink" 
                :to="`/story/node/${node.data.id}`" 
                size="small" 
                type="primary"
              >
                查看
              </n-button>
              
              <!-- 如果不是叶子节点，显示"沿此续写"按钮 -->
              <n-button 
                v-if="!(node.data as StoryNodeTreeItem).children || (node.data as StoryNodeTreeItem).children.length === 0"
                :component="RouterLink" 
                :to="`/story/write/${(node.data as StoryNodeTreeItem).book_id}?parentId=${node.data.id}&mode=continue`" 
                size="small" 
                type="default"
              >
                ✍️ 续写
              </n-button>
              
              <!-- 如果是根节点或非完结节点，显示"创建分支"按钮 -->
              <n-button 
                v-if="!(node.data as StoryNodeTreeItem).is_ending"
                :component="RouterLink" 
                :to="`/story/write/${(node.data as StoryNodeTreeItem).book_id}?parentId=${node.data.id}&mode=branch`" 
                size="small" 
                type="default"
              >
                🌿 分支
              </n-button>
            </div>
          </div>
        </template>
      </n-tree>
    </n-spin>
  </n-card>
</template>
