<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'

const route = useRoute()

// 根据路由 meta 信息动态选择布局
const layout = computed(() => {
  const layoutName = route.meta.layout || 'default'
  const layouts: Record<string, any> = {
    default: DefaultLayout,
    auth: AuthLayout,
    admin: AdminLayout,
  }
  return layouts[layoutName] || DefaultLayout
})
</script>

<template>
  <component :is="layout">
    <RouterView />
  </component>
</template>

<style scoped></style>