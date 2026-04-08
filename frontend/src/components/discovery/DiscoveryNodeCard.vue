<script setup lang="ts">
import { NButton } from 'naive-ui'
import { useRouter } from 'vue-router'
import type { DiscoveryRailItem } from '@/types/discovery'

const router = useRouter()
const props = defineProps<{
  item: DiscoveryRailItem
}>()

function openAction() {
  void router.push(props.item.action.to)
}
</script>

<template>
  <article class="ui-archive-card ui-panel-section">
    <div class="ui-archive-card__header">
      <div>
        <h3 class="ui-archive-card__title">{{ item.title }}</h3>
      </div>
      <span class="ui-chip" :data-tone="item.badgeTone || 'default'">
        {{ item.badge }}
      </span>
    </div>

    <p class="ui-archive-card__lead">
      {{ item.summary }}
    </p>

    <div class="ui-archive-card__meta">
      <span v-for="metaItem in item.meta" :key="metaItem">{{ metaItem }}</span>
    </div>

    <div v-if="item.metrics?.length" class="discovery-node-card__metrics">
      <div
        v-for="metric in item.metrics"
        :key="metric.label"
        class="discovery-node-card__metric"
      >
        <span class="discovery-node-card__metric-label">{{ metric.label }}</span>
        <span class="discovery-node-card__metric-value">{{ metric.value }}</span>
      </div>
    </div>

    <div class="ui-archive-card__footer">
      <span class="discovery-node-card__hint">{{ item.hint }}</span>
      <n-button type="primary" @click="openAction">
        {{ item.action.label }}
      </n-button>
    </div>
  </article>
</template>

<style scoped>
.discovery-node-card__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.discovery-node-card__metric {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--line-faint);
  background: rgba(255, 255, 255, 0.015);
}

.discovery-node-card__metric-label {
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.discovery-node-card__metric-value {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 13px;
}

.discovery-node-card__hint {
  color: var(--text-faint);
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
</style>
