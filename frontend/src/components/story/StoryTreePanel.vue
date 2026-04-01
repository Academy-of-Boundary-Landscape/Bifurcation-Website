<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NIcon, NTree } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import type { StoryNodeTreeItem } from '@/types/models'

interface StoryTreePanelNode extends Record<string, unknown> {
  key: string
  label: string
  children?: StoryTreePanelNode[]
  data: StoryNodeTreeItem
  isLeaf: boolean
}

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
function convertToTreeData(items: StoryNodeTreeItem[]): StoryTreePanelNode[] {
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

function expandAll() {
  expandedKeys.value = props.tree.map((node) => node.id.toString())
}
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
          <n-button size="small" @click="expandAll">
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
      />
    </n-spin>
  </n-card>
</template>
