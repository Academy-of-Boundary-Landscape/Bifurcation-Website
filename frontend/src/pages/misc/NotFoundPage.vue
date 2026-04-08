<script setup lang="ts">
import { NCard, NSpace } from 'naive-ui'
import { useRouter } from 'vue-router'

const router = useRouter()

function handleHome() {
  void router.push({ name: 'home' })
}

function handleBooks() {
  void router.push({ name: 'books' })
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-#0a0a0a">
    <n-card 
      class="w-full max-w-md bg-#1a1a1a border-#2a2a2a text-center"
      :bordered="true"
      size="huge"
      style="box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3)"
    >
      <div class="text-center py-16">
        <div class="text-9xl mb-4">❌</div>
        <h1 class="text-3xl font-bold text-white mb-2">页面未找到</h1>
        <p class="text-#666666 mb-8">您访问的页面不存在，请检查网址或返回首页。</p>
        
        <div class="flex flex-col sm:flex-row gap-4">
          <n-button 
            type="primary" 
            size="large" 
            @click="handleHome"
          >
            返回首页
          </n-button>
          
          <n-button 
            type="default" 
            size="large" 
            @click="handleBooks"
          >
            查看故事册
          </n-button>
        </div>
      </div>
      
      <template #footer>
        <div class="text-center text-#666666 text-xs">
          © 2026 分岔视界 · Bifurcation Horizon
        </div>
      </template>
    </n-card>
  </div>
</template>
