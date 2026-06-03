<script setup lang="ts">
import { NConfigProvider, NGlobalStyle, NMessageProvider, NDialogProvider } from 'naive-ui'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import { themeOverrides } from '@/theme'
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
