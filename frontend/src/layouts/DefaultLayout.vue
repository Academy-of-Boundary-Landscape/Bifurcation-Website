<script setup lang="ts">
import { computed, h } from 'vue'
import { NLayout, NLayoutHeader, NAvatar, NDropdown, NSpace, NButton } from 'naive-ui'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const menuOptions = computed(() => [
  { label: () => h(RouterLink, { to: { name: 'home' } }, { default: () => '首页' }), key: 'home' },
  { label: () => h(RouterLink, { to: { name: 'books' } }, { default: () => '故事册' }), key: 'books' },
])

const userDropdownOptions = computed(() => [
  { label: '个人中心', key: 'profile', icon: () => h('span', { class: 'text-14' }, '👤') },
  { label: '我的通知', key: 'notifications', icon: () => h('span', { class: 'text-14' }, '🔔') },
  { label: '管理台', key: 'admin', show: authStore.isAdmin, icon: () => h('span', { class: 'text-14' }, '⚙️') },
  { type: 'divider', key: 'divider' },
  { label: '退出登录', key: 'logout', icon: () => h('span', { class: 'text-14' }, '🚪') },
])

function handleSelect(key: string) {
  if (key === 'logout') {
    authStore.logout()
    router.push({ name: 'home' })
  } else if (key === 'profile') {
    router.push({ name: 'profile' })
  } else if (key === 'notifications') {
    router.push({ name: 'notifications' })
  } else if (key === 'admin') {
    router.push({ name: 'admin' })
  }
}

const activeKey = computed(() => route.name as string)
</script>

<template>
  <n-layout class="min-h-screen flex flex-col bg-#000000 text-#ffffff">
    <!-- 顶部导航 -->
    <n-layout-header bordered class="bg-#0f0f0f border-#2a2a2a px-4 h-64 flex items-center justify-between">
      <!-- Logo -->
      <RouterLink to="/" class="text-20 font-bold text-white hover:text-#8b5cf6 transition-colors">
        分岔视界
      </RouterLink>
      
      <!-- 导航菜单 (桌面端) -->
      <n-space class="hidden md:flex">
        <n-button 
          v-for="item in menuOptions" 
          :key="item.key"
          :type="activeKey === item.key ? 'primary' : 'tertiary'"
          :component="RouterLink"
          :to="item.key"
          size="large"
        >
          {{ item.label?.() }}
        </n-button>
      </n-space>
      
      <!-- 用户区域 -->
      <n-space v-if="authStore.isAuthenticated">
        <n-avatar 
          v-if="authStore.currentUser?.avatar" 
          :src="authStore.currentUser.avatar" 
          size="small"
        />
        <n-avatar v-else size="small">
          {{ authStore.currentUser?.username?.charAt(0).toUpperCase() || 'U' }}
        </n-avatar>
        <n-dropdown 
          :options="userDropdownOptions" 
          @select="handleSelect"
          placement="bottom-end"
        >
          <n-button text>
            {{ authStore.currentUser?.username || '用户' }}
          </n-button>
        </n-dropdown>
      </n-space>
      
      <n-space v-else>
        <n-button :component="RouterLink" to="/login" variant="ghost">
          登录
        </n-button>
        <n-button :component="RouterLink" to="/register" type="primary">
          注册
        </n-button>
      </n-space>
    </n-layout-header>
    
    <!-- 主内容区 -->
    <main class="flex-1 container mx-auto px-4 py-6">
      <router-view />
    </main>
    
    <!-- 页脚 -->
    <n-layout-footer bordered class="bg-#0f0f0f border-#2a2a2a py-4 text-center text-#666666">
      <p>分岔视界 Bifurcation Horizon © 2026</p>
    </n-layout-footer>
  </n-layout>
</template>