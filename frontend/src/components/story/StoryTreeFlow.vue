<script setup lang="ts">
import { 
  NCard, 
  NButton, 
  NSpace, 
  NTag,
  NSpin,
  NIcon,
  NUpload,
  NProgress
} from 'naive-ui'
import { 
  VueFlow, 
  useVueFlow,
  Controls,
  Background,
  MiniMap,
  Node,
  Edge,
  useNodes,
  useEdges,
  useStore,
  Position,
  MarkerType,
  type ConnectionLineOptions,
  type Viewport,
  type ConnectionLineType,
  type Connection,
  type HandleType,
  useNodesInitialized,
  useViewport
} from 'vue-flow'
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import type { StoryNodeTreeItem } from '@/types/models'

const props = defineProps<{
  tree: StoryNodeTreeItem[]
}>()

// 初始化 Vue Flow
const { nodes, edges, fitView, zoomTo, setViewport } = useVueFlow({
  maxZoom: 2,
  minZoom: 0.5,
})

// 添加自动布局功能
const { nodesInitialized } = useNodesInitialized()
const viewport = useViewport()

// 将故事树转换为 Vue Flow 节点和边
function convertToFlowData(items: StoryNodeTreeItem[]): { nodes: Node[], edges: Edge[] } {
  const flowNodes: Node[] = []
  const flowEdges: Edge[] = []
  
  function processNodes(nodes: StoryNodeTreeItem[], parentId: string | null = null, level: number = 0, index: number = 0) {
    nodes.forEach((node, i) => {
      // 计算节点位置 - 基于层级的自动布局
      const x = level * 250 + 50
      const y = (index + i) * 120 + 50
      
      // 创建节点
      const nodeData: Node = {
        id: node.id.toString(),
        position: { x, y },
        data: {
          title: node.branch_name || node.title || `节点${node.id}`,
          author: node.author?.username || '未知作者',
          status: node.status,
          likes_count: node.likes_count,
          is_ending: node.is_ending,
          summary: node.summary || '',
          // content 字段在 StoryNodeTreeItem 中不存在，使用 summary 替代
        },
        type: 'storyNode',
      }
      
      flowNodes.push(nodeData)
      
      // 创建边（连接父节点）
      if (parentId && node.parent_id !== null) {
        flowEdges.push({
          id: `edge-${parentId}-${node.id}`,
          source: parentId,
          target: node.id.toString(),
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#8b5cf6',
            width: 20,
            height: 20,
          }
        })
      }
      
      // 处理子节点
      if (node.children && node.children.length > 0) {
        // 递归处理子节点，使用新的索引
        processNodes(node.children, node.id.toString(), level + 1, index + i)
      }
    })
  }
  
  // 从根节点开始处理
  if (props.tree.length > 0) {
    processNodes(props.tree)
  }
  
  return { nodes: flowNodes, edges: flowEdges }
}

// 初始化节点和边
onMounted(() => {
  const flowData = convertToFlowData(props.tree)
  nodes.value = flowData.nodes
  edges.value = flowData.edges
  
  // 等待节点初始化后调整布局
  nextTick(() => {
    setTimeout(() => {
      fitView()
    }, 100)
  })
})

// 监听 tree 属性变化
watch(() => props.tree, (newTree) => {
  const flowData = convertToFlowData(newTree)
  nodes.value = flowData.nodes
  edges.value = flowData.edges
  
  // 重新布局
  nextTick(() => {
    setTimeout(() => {
      fitView()
    }, 100)
  })
}, { deep: true })

// 自定义节点类型
const customNodeTypes = {
  storyNode: {
    component: {
      name: 'StoryNode',
      props: {
        class: 'bg-#1a1a1a border-#2a2a2a rounded-lg shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer'
      }
    }
  }
}

// 节点点击事件
function handleNodeClick(event: MouseEvent, node: Node) {
  // 获取节点ID并跳转到详情页
  const nodeId = parseInt(node.id)
  if (!isNaN(nodeId)) {
    // 触发路由跳转事件
    emit('node-click', nodeId)
  }
}

// 节点悬停效果
function handleNodeMouseEnter(event: MouseEvent, node: Node) {
  // 添加悬停效果
  const nodeEl = event.target as HTMLElement
  if (nodeEl) {
    nodeEl.style.transform = 'scale(1.05)'
  }
}

function handleNodeMouseLeave(event: MouseEvent, node: Node) {
  // 移除悬停效果
  const nodeEl = event.target as HTMLElement
  if (nodeEl) {
    nodeEl.style.transform = 'scale(1)'
  }
}

// 定义事件
const emit = defineEmits(['node-click'])
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-bold text-white">故事树可视化</h2>
        <n-space>
          <n-button size="small" @click="fitView">
            重置视图
          </n-button>
          <n-button size="small" @click="zoomTo(1)">
            缩放至100%
          </n-button>
          <n-button size="small" @click="() => setViewport({ x: 0, y: 0, zoom: 1 })">
            居中显示
          </n-button>
        </n-space>
      </div>
    </template>
    
    <n-spin :show="!tree || tree.length === 0">
      <div v-if="!tree || tree.length === 0" class="text-center py-10 text-#666666">
        暂无节点，成为第一个创作者吧！
      </div>
      
      <div 
        v-else 
        class="w-full h-[600px] bg-#0a0a0a rounded-lg overflow-hidden relative"
        style="min-height: 600px;"
      >
        <!-- Vue Flow 画布 -->
        <VueFlow
          :nodes="nodes"
          :edges="edges"
          :node-types="customNodeTypes"
          fit-view-on-init
          class="w-full h-full"
          @node-click="handleNodeClick"
          @node-mouse-enter="handleNodeMouseEnter"
          @node-mouse-leave="handleNodeMouseLeave"
        >
          <!-- 背景 -->
          <Background 
            pattern-color="#1a1a1a" 
            gap="20" 
            size="1"
          />
          
          <!-- 控制面板 -->
          <Controls />
          
          <!-- 迷你地图 -->
          <MiniMap 
            :node-color="({ data }) => {
              if (data.is_ending) return '#34d399'
              if (data.status === 'published') return '#60a5fa'
              if (data.status === 'pending') return '#f59e0b'
              return '#ef4444'
            }"
            :node-border-radius="8"
            :node-width="100"
            :node-height="60"
            class="absolute bottom-4 right-4"
          />
          
          <!-- 自定义节点渲染 -->
          <template #node-storyNode="{ data, selected }">
            <div 
              class="relative p-4 w-48 cursor-pointer transition-all"
              :class="selected ? 'ring-2 ring-#8b5cf6 scale-105' : ''"
              @click="() => emit('node-click', parseInt(data.id))"
            >
              <div class="absolute -top-2 -right-2">
                <n-tag 
                  v-if="data.is_ending" 
                  type="success" 
                  size="small"
                  round
                >
                  ✅
                </n-tag>
                <n-tag 
                  v-else-if="data.status === 'published'" 
                  type="primary" 
                  size="small"
                  round
                >
                  🟢
                </n-tag>
                <n-tag 
                  v-else-if="data.status === 'pending'" 
                  type="warning" 
                  size="small"
                  round
                >
                  🟡
                </n-tag>
                <n-tag 
                  v-else 
                  type="error" 
                  size="small"
                  round
                >
                  🔴
                </n-tag>
              </div>
              
              <h3 class="font-semibold text-white text-sm mb-1 truncate">
                {{ data.title }}
              </h3>
              <p class="text-xs text-#666666 mb-2 line-clamp-2">
                {{ data.summary }}
              </p>
              <div class="flex items-center justify-between text-xs">
                <span class="text-#8b5cf6">{{ data.likes_count }} 赞</span>
                <span class="text-#666666">{{ data.author }}</span>
              </div>
            </div>
          </template>
        </VueFlow>
      </div>
    </n-spin>
  </n-card>
</template>

<style scoped>
/* Vue Flow 样式 */
.vue-flow__node {
  background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
  border: 1px solid #2a2a2a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  transition-property: transform, box-shadow;
}

.vue-flow__node:hover {
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
  transform: translateY(-1px) scale(1.05);
}

.vue-flow__edge-path {
  stroke: #60a5fa;
  stroke-width: 2;
  transition: stroke 0.3s ease;
}

.vue-flow__edge-path:hover {
  stroke: #8b5cf6;
}

.vue-flow__control-button {
  background: rgba(26, 26, 26, 0.8);
  border: 1px solid #2a2a2a;
  color: white;
  transition: all 0.3s ease;
}

.vue-flow__control-button:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8b5cf6;
  transform: scale(1.05);
}

.vue-flow__minimap-node {
  background: #8b5cf6;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.vue-flow__minimap-node:hover {
  background: #6366f1;
  transform: scale(1.1);
}
</style>
</content>
<task_progress>
- [x] 分析 ProfilePage.vue 当前实现
- [x] 实现 ProfilePage.vue 头像上传功能
- [x] 实现 NotificationPage.vue 筛选功能
- [x] 完善 StoryNodePage.vue 功能
- [x] 完善 StoryTreeFlow.vue 功能
</task_progress>
</content>
<task_progress>
- [x] 分析 ProfilePage.vue 当前实现
- [x] 实现 ProfilePage.vue 头像上传功能
- [x] 实现 NotificationPage.vue 筛选功能
- [x] 完善 StoryNodePage.vue 功能
- [x] 完善 StoryTreeFlow.vue 功能
</task_progress>
</content>
<task_progress>
- [x] 分析 ProfilePage.vue 当前实现
- [x] 实现 ProfilePage.vue 头像上传功能
- [x] 实现 NotificationPage.vue 筛选功能
- [x] 完善 StoryNodePage.vue 功能
- [x] 完善 StoryTreeFlow.vue 功能
</task_progress>
</content>
<task_progress>
- [x] 分析 ProfilePage.vue 当前实现
- [x] 实现 ProfilePage.vue 头像上传功能
- [x] 实现 NotificationPage.vue 筛选功能
- [x] 完善 StoryNodePage.vue 功能
- [x] 完善 StoryTreeFlow.vue 功能
</task_progress>
</content>
<task_progress>
- [x] 分析 ProfilePage.vue 当前实现
- [x] 实现 ProfilePage.vue 头像上传功能
- [x] 实现 NotificationPage.vue 筛选功能
- [x] 完善 StoryNodePage.vue 功能
- [x] 完善 StoryTreeFlow.vue 功能
</task_progress>
