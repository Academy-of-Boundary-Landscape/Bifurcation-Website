<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { NButton, NCard, NSpace, NSpin } from 'naive-ui'

import StoryTreeFlowNode from '@/components/story/StoryTreeFlowNode.vue'
import type { StoryNodeTreeItem } from '@/types/models'

type FlowNodeStatus = StoryNodeTreeItem['status']

interface FlowStoryNodeData {
  sourceId: number
  title: string
  author: string
  status: FlowNodeStatus
  likes_count: number
  is_ending: boolean
  summary: string
  childBranchNames: string[]
  childCount: number
}

interface FlowPosition {
  x: number
  y: number
}

interface FlowStoryNode {
  id: string
  position: FlowPosition
  data: FlowStoryNodeData
}

interface FlowStoryEdge {
  id: string
  source: string
  target: string
}

const NODE_WIDTH = 124
const NODE_HEIGHT = 124
const HORIZONTAL_GAP = 184
const VERTICAL_GAP = 158
const SINGLE_CHILD_OFFSET = 84
const PADDING = 80
const MIN_ZOOM = 0.45
const MAX_ZOOM = 1.8

const props = defineProps<{
  tree: StoryNodeTreeItem[]
  selectedNodeId?: number | null
  isLoading?: boolean
}>()

const emit = defineEmits<{
  'node-click': [nodeId: number]
}>()

const containerRef = ref<HTMLElement | null>(null)
const zoom = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const dragOriginX = ref(0)
const dragOriginY = ref(0)

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function convertToFlowData(items: StoryNodeTreeItem[]): { nodes: FlowStoryNode[]; edges: FlowStoryEdge[] } {
  const flowNodes: FlowStoryNode[] = []
  const flowEdges: FlowStoryEdge[] = []

  function placeNode(node: StoryNodeTreeItem, level: number, parentId: string | null, cursorY: number): number {
    const x = level * HORIZONTAL_GAP + PADDING
    const nodeId = node.id.toString()

    if (parentId) {
      flowEdges.push({
        id: `edge-${parentId}-${node.id}`,
        source: parentId,
        target: nodeId,
      })
    }

    const children = node.children ?? []
    let y = cursorY

    if (children.length === 1) {
      const child = children[0]!
      const childStartY = cursorY + SINGLE_CHILD_OFFSET
      const nextChildY = placeNode(child, level + 1, nodeId, childStartY)
      y = cursorY
      cursorY = Math.max(nextChildY, cursorY + VERTICAL_GAP)
    } else if (children.length > 1) {
      let nextChildY = cursorY
      const childCenters: number[] = []

      for (const child of children) {
        const childStartY = nextChildY
        nextChildY = placeNode(child, level + 1, nodeId, nextChildY)
        childCenters.push((childStartY + nextChildY - VERTICAL_GAP) / 2)
      }

      y = childCenters.reduce((sum, value) => sum + value, 0) / childCenters.length
      cursorY = nextChildY
    } else {
      cursorY += VERTICAL_GAP
    }

    flowNodes.push({
      id: nodeId,
      position: { x, y: y + PADDING },
      data: {
        sourceId: node.id,
        title: node.branch_name || node.title || `节点${node.id}`,
        author: node.author?.username || '未知作者',
        status: node.status,
        likes_count: node.likes_count,
        is_ending: node.is_ending,
        summary: node.summary || '',
        childBranchNames: children
          .map((child) => child.branch_name || child.title || `节点${child.id}`)
          .filter((label) => Boolean(label))
          .slice(0, 4),
        childCount: children.length,
      },
    })

    return cursorY
  }

  let nextRootY = 0
  for (const rootNode of items) {
    nextRootY = placeNode(rootNode, 0, null, nextRootY)
    nextRootY += VERTICAL_GAP * 0.35
  }

  return { nodes: flowNodes, edges: flowEdges }
}

const flowData = computed(() => convertToFlowData(props.tree))
const nodes = computed(() => flowData.value.nodes)
const edges = computed(() => flowData.value.edges)

const nodeMap = computed(() => {
  return new Map(nodes.value.map((node) => [node.id, node]))
})

const canvasWidth = computed(() => {
  if (!nodes.value.length) return 960
  const maxX = Math.max(...nodes.value.map((node) => node.position.x + NODE_WIDTH))
  return maxX + PADDING
})

const canvasHeight = computed(() => {
  if (!nodes.value.length) return 560
  const maxY = Math.max(...nodes.value.map((node) => node.position.y + NODE_HEIGHT))
  return maxY + PADDING
})

const selectedNode = computed(() => {
  if (props.selectedNodeId == null) return null
  return nodes.value.find((node) => node.data.sourceId === props.selectedNodeId) ?? null
})

const renderedEdges = computed(() => {
  return edges.value
    .map((edge) => {
      const source = nodeMap.value.get(edge.source)
      const target = nodeMap.value.get(edge.target)
      if (!source || !target) return null

      return {
        id: edge.id,
        x1: source.position.x + NODE_WIDTH,
        y1: source.position.y + NODE_HEIGHT / 2,
        x2: target.position.x,
        y2: target.position.y + NODE_HEIGHT / 2,
        sourceChildCount: source.data.childCount,
        path: [
          `M ${source.position.x + NODE_WIDTH} ${source.position.y + NODE_HEIGHT / 2}`,
          `C ${source.position.x + NODE_WIDTH + 52} ${source.position.y + NODE_HEIGHT / 2},`,
          `${target.position.x - 52} ${target.position.y + NODE_HEIGHT / 2},`,
          `${target.position.x} ${target.position.y + NODE_HEIGHT / 2}`,
        ].join(' '),
      }
    })
    .filter((edge): edge is NonNullable<typeof edge> => edge !== null)
})

function setViewport(nextX: number, nextY: number, nextZoom: number) {
  zoom.value = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM)
  offsetX.value = nextX
  offsetY.value = nextY
}

function fitView() {
  const container = containerRef.value
  if (!container) return

  const width = container.clientWidth || 1
  const height = container.clientHeight || 1
  const fitZoom = clamp(
    Math.min(width / canvasWidth.value, height / canvasHeight.value) * 0.92,
    MIN_ZOOM,
    MAX_ZOOM,
  )

  const nextX = (width - canvasWidth.value * fitZoom) / 2
  const nextY = (height - canvasHeight.value * fitZoom) / 2
  setViewport(nextX, nextY, fitZoom)
}

function centerOnNode(nodeId: number) {
  const container = containerRef.value
  if (!container) return
  const node = nodes.value.find((item) => item.data.sourceId === nodeId)
  if (!node) return

  const width = container.clientWidth || 1
  const height = container.clientHeight || 1
  const nextX = width / 2 - (node.position.x + NODE_WIDTH / 2) * zoom.value
  const nextY = height / 2 - (node.position.y + NODE_HEIGHT / 2) * zoom.value
  setViewport(nextX, nextY, zoom.value)
}

function zoomTo(nextZoom: number) {
  const container = containerRef.value
  if (!container) {
    zoom.value = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM)
    return
  }

  const rect = container.getBoundingClientRect()
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const clampedZoom = clamp(nextZoom, MIN_ZOOM, MAX_ZOOM)
  const worldX = (centerX - offsetX.value) / zoom.value
  const worldY = (centerY - offsetY.value) / zoom.value
  setViewport(centerX - worldX * clampedZoom, centerY - worldY * clampedZoom, clampedZoom)
}

function resetViewport() {
  fitView()
}

function beginDrag(event: MouseEvent) {
  isDragging.value = true
  dragStartX.value = event.clientX
  dragStartY.value = event.clientY
  dragOriginX.value = offsetX.value
  dragOriginY.value = offsetY.value
}

function handleGlobalMouseMove(event: MouseEvent) {
  if (!isDragging.value) return
  offsetX.value = dragOriginX.value + (event.clientX - dragStartX.value)
  offsetY.value = dragOriginY.value + (event.clientY - dragStartY.value)
}

function endDrag() {
  isDragging.value = false
}

function handleWheel(event: WheelEvent) {
  event.preventDefault()
  const container = containerRef.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  const pointerX = event.clientX - rect.left
  const pointerY = event.clientY - rect.top
  const factor = event.deltaY > 0 ? 0.92 : 1.08
  const nextZoom = clamp(zoom.value * factor, MIN_ZOOM, MAX_ZOOM)
  const worldX = (pointerX - offsetX.value) / zoom.value
  const worldY = (pointerY - offsetY.value) / zoom.value
  setViewport(pointerX - worldX * nextZoom, pointerY - worldY * nextZoom, nextZoom)
}

function emitNodeClick(sourceId: number) {
  emit('node-click', sourceId)
}

function isSelectedNode(sourceId: number) {
  return props.selectedNodeId === sourceId
}

watch(
  () => props.tree,
  async () => {
    await nextTick()
    fitView()
  },
  { deep: true, immediate: true },
)

watch(
  () => props.selectedNodeId,
  async (nodeId) => {
    if (nodeId == null) return
    await nextTick()
    centerOnNode(nodeId)
  },
)

onMounted(() => {
  window.addEventListener('mousemove', handleGlobalMouseMove)
  window.addEventListener('mouseup', endDrag)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', handleGlobalMouseMove)
  window.removeEventListener('mouseup', endDrag)
})
</script>

<template>
  <n-card class="ui-shell-panel" :bordered="false">
    <template #header>
      <div class="flex items-center justify-between gap-4">
        <div>
          <p class="ui-shell-kicker">Story Graph</p>
          <h2 class="ui-shell-title mt-2 text-[1.4rem] uppercase">故事树可视化</h2>
        </div>
        <n-space>
          <n-button size="small" @click="fitView">
            自适应视图
          </n-button>
          <n-button size="small" @click="zoomTo(1)">
            缩放至100%
          </n-button>
          <n-button size="small" @click="zoomTo(zoom * 1.15)">
            放大
          </n-button>
          <n-button size="small" @click="zoomTo(zoom / 1.15)">
            缩小
          </n-button>
          <n-button size="small" @click="resetViewport">
            重置视图
          </n-button>
        </n-space>
      </div>
    </template>

    <n-spin :show="Boolean(isLoading)">
      <div v-if="!isLoading && (!tree || tree.length === 0)" class="ui-status-note text-center">
        暂无节点，成为第一个创作者吧！
      </div>

      <div
        v-else-if="!isLoading"
        ref="containerRef"
        class="story-flow-canvas ui-shell-panel ui-shell-grid"
        :class="{ 'story-flow-canvas--dragging': isDragging }"
        @mousedown="beginDrag"
        @wheel="handleWheel"
      >
        <div
          class="story-flow-stage"
          :style="{
            width: `${canvasWidth}px`,
            height: `${canvasHeight}px`,
            transform: `translate(${offsetX}px, ${offsetY}px) scale(${zoom})`,
          }"
        >
          <svg class="story-flow-stage__edges" :width="canvasWidth" :height="canvasHeight">
            <defs>
              <filter id="story-flow-edge-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="1.8" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <path
              v-for="edge in renderedEdges"
              :key="edge.id"
              :d="edge.path"
              class="story-flow-stage__edge"
              :class="{ 'story-flow-stage__edge--single-child': edge.sourceChildCount === 1 }"
              filter="url(#story-flow-edge-glow)"
            />
            <circle
              v-for="edge in renderedEdges"
              :key="`${edge.id}-dot`"
              :cx="edge.x2"
              :cy="edge.y2"
              r="2.6"
              class="story-flow-stage__edge-dot"
            />
          </svg>

          <button
            v-for="node in nodes"
            :key="node.id"
            type="button"
            class="story-flow-stage__node"
            :style="{
              left: `${node.position.x}px`,
              top: `${node.position.y}px`,
              width: `${NODE_WIDTH}px`,
            }"
            @click.stop="emitNodeClick(node.data.sourceId)"
          >
            <story-tree-flow-node
              :author="node.data.author"
              :is-ending="node.data.is_ending"
              :likes-count="node.data.likes_count"
              :selected="isSelectedNode(node.data.sourceId)"
              :status="node.data.status"
              :summary="node.data.summary"
              :title="node.data.title"
              :child-branch-names="node.data.childBranchNames"
            />
          </button>
        </div>

        <div class="story-flow-overlay">
          <div class="story-flow-overlay__badge">ZOOM {{ Math.round(zoom * 100) }}%</div>
          <div v-if="selectedNode" class="story-flow-overlay__badge">
            FOCUS #{{ selectedNode.data.sourceId }}
          </div>
        </div>
      </div>
    </n-spin>
  </n-card>
</template>

<style scoped>
.story-flow-canvas {
  position: relative;
  height: 600px;
  overflow: visible;
  border-radius: var(--radius-lg);
  cursor: grab;
  user-select: none;
}

.story-flow-canvas--dragging {
  cursor: grabbing;
}

.story-flow-stage {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  will-change: transform;
}

.story-flow-stage__edges {
  position: absolute;
  inset: 0;
  overflow: visible;
  pointer-events: none;
}

.story-flow-stage__edge {
  fill: none;
  stroke: rgba(230, 234, 237, 0.64);
  stroke-width: 1.45;
  stroke-linecap: round;
}

.story-flow-stage__edge--single-child {
  stroke-dasharray: 0;
  stroke-width: 1.6;
  stroke: rgba(236, 240, 243, 0.74);
}

.story-flow-stage__edge-dot {
  fill: rgba(239, 242, 245, 0.82);
  opacity: 0.9;
}

.story-flow-stage__node {
  position: absolute;
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  overflow: visible;
}

.story-flow-overlay {
  position: absolute;
  top: 14px;
  right: 14px;
  display: grid;
  gap: 8px;
  pointer-events: none;
}

.story-flow-overlay__badge {
  padding: 6px 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(5, 7, 10, 0.76);
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
</style>
