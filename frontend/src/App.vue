<script setup lang="ts">
import { NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider } from 'naive-ui'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

// 深色主题配置
const themeOverrides = {
  common: {
    primaryColor: '#8b5cf6',
    primaryColorHover: '#7c3aed',
    primaryColorPressed: '#6d28d9',
    borderRadius: '8px',
  },
}
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides" abstract>
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <DefaultLayout />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>