<script setup lang="ts">
import { NLayout } from 'naive-ui'
</script>

<template>
  <n-layout-footer class="bg-#1a1a1a border-t border-#2a2a2a flex items-center justify-center py-4 text-#666666 text-sm">
    <div class="flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-8">
      <span>© 2026 分岔视界 · Bifurcation Horizon</span>
      <div class="flex space-x-4">
        <a href="#" class="hover:text-white transition-colors">关于我们</a>
        <a href="#" class="hover:text-white transition-colors">联系方式</a>
        <a href="#" class="hover:text-white transition-colors">隐私政策</a>
      </div>
    </div>
  </n-layout-footer>
</template>

<style scoped>
.n-layout-footer {
  height: 64px;
}
</style>