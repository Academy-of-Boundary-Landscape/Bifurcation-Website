<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  author: string
  childBranchNames: string[]
  isEnding: boolean
  likesCount: number
  selected: boolean
  status: string
  summary: string
  title: string
}>()

const emit = defineEmits<{
  click: []
}>()

function handleClick() {
  emit('click')
}

const statusLabel = computed(() => {
  if (props.isEnding) {
    return '已完结'
  }

  if (props.status === 'published') {
    return '已发布'
  }

  if (props.status === 'pending') {
    return '待审核'
  }

  if (props.status === 'archived') {
    return '已归档'
  }

  return props.status
})

const authorLabel = computed(() => props.author.trim().slice(0, 16) || 'UNKNOWN')
const likesLabel = computed(() => `${props.likesCount} likes`)
const shapeClass = computed(() => {
  if (props.isEnding) return 'story-tree-node--shape-diamond'
  if (props.status === 'pending') return 'story-tree-node--shape-hex'
  if (props.status === 'archived') return 'story-tree-node--shape-square'
  return 'story-tree-node--shape-circle'
})
const likesTier = computed(() => {
  if (props.likesCount >= 20) return 'high'
  if (props.likesCount >= 8) return 'mid'
  return 'low'
})
const childBranchPreview = computed(() => props.childBranchNames.slice(0, 3))
</script>

<template>
  <div
    class="story-tree-node transition-[transform,border-color,box-shadow,background] duration-200 hover:-translate-y-1"
    :class="[
      selected ? 'story-tree-node--selected' : '',
      isEnding ? 'story-tree-node--ending' : '',
      `story-tree-node--${status}`,
      `story-tree-node--likes-${likesTier}`,
      shapeClass,
    ]"
    @click="handleClick"
  >
    <div class="story-tree-node__halo" />
    <div class="story-tree-node__ring story-tree-node__ring--outer" />
    <div class="story-tree-node__ring story-tree-node__ring--inner" />

    <div class="story-tree-node__core">
      <div class="story-tree-node__glyph">
        <span class="story-tree-node__glyph-mark">{{ isEnding ? '◎' : '◉' }}</span>
      </div>

      <h3 class="story-tree-node__title" :title="props.title">
        {{ title }}
      </h3>

      <p class="story-tree-node__author" :title="props.author">
        {{ authorLabel }}
      </p>
    </div>

    <div class="story-tree-node__tooltip" role="tooltip">
      <div class="story-tree-node__tooltip-grid">
        <div class="story-tree-node__tooltip-row">
          <span class="story-tree-node__tooltip-label">标题</span>
          <p class="story-tree-node__tooltip-value story-tree-node__tooltip-value--title">
            {{ props.title }}
          </p>
        </div>
        <div class="story-tree-node__tooltip-row">
          <span class="story-tree-node__tooltip-label">作者</span>
          <p class="story-tree-node__tooltip-value">{{ props.author }}</p>
        </div>
        <div class="story-tree-node__tooltip-row">
          <span class="story-tree-node__tooltip-label">状态</span>
          <p class="story-tree-node__tooltip-value">{{ statusLabel }}</p>
        </div>
        <div class="story-tree-node__tooltip-row">
          <span class="story-tree-node__tooltip-label">热度</span>
          <p class="story-tree-node__tooltip-value">{{ likesLabel }}</p>
        </div>
        <div v-if="childBranchPreview.length" class="story-tree-node__tooltip-row">
          <span class="story-tree-node__tooltip-label">后续分支</span>
          <div class="story-tree-node__tooltip-list">
            <p
              v-for="branchName in childBranchPreview"
              :key="branchName"
              class="story-tree-node__tooltip-branch"
            >
              {{ branchName }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.story-tree-node {
  position: relative;
  display: flex;
  width: 124px;
  height: 124px;
  align-items: center;
  justify-content: center;
  overflow: visible;
  padding: 11px 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.085), rgba(255, 255, 255, 0.014) 48%, rgba(255, 255, 255, 0) 72%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.025), rgba(255, 255, 255, 0.008));
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.035),
    0 14px 30px rgba(0, 0, 0, 0.2);
  text-align: center;
  cursor: pointer;
}

.story-tree-node--shape-circle {
  border-radius: 999px;
}

.story-tree-node--shape-square {
  border-radius: 18px;
}

.story-tree-node--shape-hex {
  clip-path: polygon(22% 4%, 78% 4%, 96% 50%, 78% 96%, 22% 96%, 4% 50%);
}

.story-tree-node--shape-diamond {
  clip-path: polygon(50% 2%, 98% 50%, 50% 98%, 2% 50%);
}

.story-tree-node:hover {
  z-index: 8;
}

.story-tree-node--selected {
  border-color: rgba(255, 255, 255, 0.28);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.08),
    0 0 32px rgba(255, 255, 255, 0.12),
    0 18px 40px rgba(0, 0, 0, 0.28);
}

.story-tree-node--published .story-tree-node__status,
.story-tree-node--published .story-tree-node__glyph,
.story-tree-node--published .story-tree-node__author {
  color: rgba(221, 255, 221, 0.92);
}

.story-tree-node--pending .story-tree-node__glyph {
  border-color: rgba(255, 236, 179, 0.3);
  background: rgba(255, 236, 179, 0.05);
}

.story-tree-node--archived {
  border-color: rgba(196, 196, 196, 0.16);
}

.story-tree-node--archived .story-tree-node__glyph {
  opacity: 0.62;
}

.story-tree-node--ending {
  border-style: dashed;
}

.story-tree-node--likes-low {
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.03),
    0 12px 24px rgba(0, 0, 0, 0.18);
}

.story-tree-node--likes-mid {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.018) 48%, rgba(255, 255, 255, 0) 72%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.032), rgba(255, 255, 255, 0.01));
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.04),
    0 15px 28px rgba(0, 0, 0, 0.22),
    0 0 20px rgba(255, 255, 255, 0.035);
}

.story-tree-node--likes-high {
  background:
    radial-gradient(circle at 50% 36%, rgba(255, 255, 255, 0.13), rgba(255, 255, 255, 0.024) 48%, rgba(255, 255, 255, 0) 72%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.012));
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.05),
    0 18px 34px rgba(0, 0, 0, 0.24),
    0 0 28px rgba(255, 255, 255, 0.05);
}

.story-tree-node__halo {
  position: absolute;
  inset: 9px;
  border-radius: 999px;
  background: radial-gradient(circle at 50% 45%, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0) 70%);
  opacity: 0.65;
}

.story-tree-node__ring {
  position: absolute;
  pointer-events: none;
}

.story-tree-node--shape-circle .story-tree-node__ring,
.story-tree-node--shape-circle .story-tree-node__halo {
  border-radius: 999px;
}

.story-tree-node--shape-square .story-tree-node__ring,
.story-tree-node--shape-square .story-tree-node__halo {
  border-radius: 16px;
}

.story-tree-node--shape-hex .story-tree-node__ring,
.story-tree-node--shape-hex .story-tree-node__halo {
  clip-path: polygon(22% 4%, 78% 4%, 96% 50%, 78% 96%, 22% 96%, 4% 50%);
}

.story-tree-node--shape-diamond .story-tree-node__ring,
.story-tree-node--shape-diamond .story-tree-node__halo {
  clip-path: polygon(50% 2%, 98% 50%, 50% 98%, 2% 50%);
}

.story-tree-node__ring--outer {
  inset: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.story-tree-node__ring--inner {
  inset: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.story-tree-node__author {
  margin: 0;
  max-width: 82px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-faint);
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.story-tree-node__title {
  margin: 0;
  overflow: hidden;
  font-family: var(--font-display);
  max-width: 84px;
  font-size: 11px;
  line-height: 1.18;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.story-tree-node__core {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  gap: 8px;
}

.story-tree-node__glyph {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.03);
}

.story-tree-node__glyph-mark {
  color: rgba(255, 255, 255, 0.86);
  font-size: 10px;
  line-height: 1;
}

.story-tree-node__tooltip {
  position: absolute;
  top: 50%;
  left: calc(100% + 16px);
  z-index: 12;
  width: 220px;
  padding: 14px 14px 13px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(10, 10, 10, 0.96), rgba(18, 18, 18, 0.94)),
    rgba(0, 0, 0, 0.92);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.035),
    0 18px 36px rgba(0, 0, 0, 0.42),
    0 0 22px rgba(255, 255, 255, 0.04);
  opacity: 0;
  pointer-events: none;
  transform: translateY(-50%) translateX(-8px);
  transition: opacity 160ms ease, transform 160ms ease;
  backdrop-filter: blur(10px);
}

.story-tree-node__tooltip::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -8px;
  width: 12px;
  height: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(12, 12, 12, 0.96);
  transform: translateY(-50%) rotate(-45deg);
}

.story-tree-node:hover .story-tree-node__tooltip {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}

.story-tree-node__tooltip-grid {
  display: grid;
  gap: 10px;
}

.story-tree-node__tooltip-row {
  display: grid;
  gap: 4px;
}

.story-tree-node__tooltip-label {
  font-size: 9px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.story-tree-node__tooltip-value {
  margin: 0;
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.45;
  word-break: break-word;
}

.story-tree-node__tooltip-value--title {
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.story-tree-node__tooltip-list {
  display: grid;
  gap: 6px;
}

.story-tree-node__tooltip-branch {
  margin: 0;
  padding-left: 10px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.45;
  position: relative;
}

.story-tree-node__tooltip-branch::before {
  content: '';
  position: absolute;
  top: 8px;
  left: 0;
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
}
</style>
