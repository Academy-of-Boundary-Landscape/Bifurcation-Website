<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-900 flex flex-col">
    <!-- 顶部导航 -->
    <AppHeader />
    
    <!-- 主内容区 -->
    <main class="flex-1">
      <RouterView />
    </main>
    
    <!-- 页脚 -->
    <AppFooter />
  </div>
</template>

<style scoped></style>