<script setup lang="ts">
import { NButton, NSpin } from 'naive-ui'
import { useRouter } from 'vue-router'
import DiscoveryNodeCard from '@/components/discovery/DiscoveryNodeCard.vue'
import type { DiscoveryRailProps } from '@/types/discovery'

const router = useRouter()
const props = defineProps<DiscoveryRailProps>()

function openRailAction() {
  if (!props.actionTo) return
  void router.push(props.actionTo)
}
</script>

<template>
  <section class="ui-page-section ui-shell-panel">
    <div class="ui-page-section__header">
      <div>
        <p class="ui-shell-kicker">{{ kicker }}</p>
        <h2 class="ui-shell-title">{{ title }}</h2>
        <p v-if="description" class="ui-page-section__lead">
          {{ description }}
        </p>
      </div>
      <n-button
        v-if="actionLabel && actionTo"
        tertiary
        @click="openRailAction"
      >
        {{ actionLabel }}
      </n-button>
    </div>

    <div v-if="loading" class="discovery-rail__state">
      <n-spin size="large" />
    </div>
    <div v-else-if="error" class="ui-status-note ui-status-note--danger">
      加载失败：{{ error.message }}
    </div>
    <div v-else-if="!items?.length" class="ui-status-note">
      {{ emptyText || '当前暂无内容。' }}
    </div>
    <div v-else class="ui-card-list ui-card-list--books">
      <DiscoveryNodeCard
        v-for="item in items"
        :key="item.id"
        :item="item"
      />
    </div>
  </section>
</template>

<style scoped>
.discovery-rail__state {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
</style>
