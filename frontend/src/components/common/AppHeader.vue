<script setup lang="ts">
import { NLayout, NMenu, NIcon, NAvatar } from 'naive-ui'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const menuOptions = [
  {
    label: '首页',
    key: 'home',
    path: '/',
  },
  {
    label: '故事册',
    key: 'books',
    path: '/books',
  },
  {
    label: '创作说明',
    key: 'rules',
    path: '/rules',
  },
  {
    label: '排行榜',
    key: 'ranking',
    path: '/ranking',
  }
]

const activeKey = computed(() => {
  const path = route.path
  if (path === '/') return 'home'
  if (path.startsWith('/books')) return 'books'
  if (path.startsWith('/story')) return 'story'
  if (path === '/rules') return 'rules'
  if (path === '/ranking') return 'ranking'
  return ''
})

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <n-layout-header class="bg-#1a1a1a border-b border-#2a2a2a flex items-center px-6">
    <div class="flex items-center flex-1">
      <RouterLink 
        to="/" 
        class="text-xl font-bold text-white hover:text-#8b5cf6 transition-colors"
      >
        分岔视界
      </RouterLink>
    </div>
    
    <div class="hidden md:flex items-center space-x-6">
      <n-menu 
        :options="menuOptions" 
        :value="activeKey"
        :indent="0"
        @update:value="(key) => router.push(menuOptions.find(o => o.key === key)?.path || '/')"
        class="flex space-x-4"
      >
        <template #option="{ option }">
          <router-link 
            :to="option.path" 
            class="text-#666666 hover:text-white transition-colors"
            :class="activeKey === option.key ? 'text-white' : ''"
          >
            {{ option.label }}
          </router-link>
        </template>
      </n-menu>
    </div>
    
    <div class="flex items-center space-x-4">
      <!-- 通知铃铛 -->
      <button 
        class="text-#666666 hover:text-white transition-colors"
        v-if="authStore.isAuthenticated"
      >
        <i class="ri-notification-3-line text-xl"></i>
      </button>
      
      <!-- 用户头像 -->
      <div v-if="authStore.isAuthenticated" class="flex items-center space-x-2">
        <n-avatar 
          :size="32"
          :src="authStore.currentUser?.avatar ?? undefined"
        >
          {{ authStore.currentUser?.username?.charAt(0).toUpperCase() }}
        </n-avatar>
        <span class="text-#d9d9d9 text-sm">{{ authStore.currentUser?.username }}</span>
      </div>
      
      <!-- 登录/注册按钮 -->
      <div v-else class="flex space-x-2">
        <router-link 
          :to="{ name: 'login' }" 
          class="text-#666666 hover:text-white transition-colors"
        >
          登录
        </router-link>
        <router-link 
          :to="{ name: 'register' }" 
          class="text-#666666 hover:text-white transition-colors"
        >
          注册
        </router-link>
      </div>
    </div>
  </n-layout-header>
</template>

<style scoped>
.n-layout-header {
  height: 64px;
}
</style>
