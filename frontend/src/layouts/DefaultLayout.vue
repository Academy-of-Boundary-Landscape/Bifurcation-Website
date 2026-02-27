<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
</script>

<template>
  <div class="min-h-screen bg-bg-base text-text-primary">
    <AppHeader />
    <main class="mx-auto w-full max-w-[1440px] px-6 py-6 md:px-8">
      <RouterView />
    </main>
  </div>
</template>

<style scoped></style>