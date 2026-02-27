<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppButton from '@/components/common/AppButton.vue'
import logoUrl from '@/assets/images/logo-tech.svg'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { label: '首页', to: '/' },
  { label: '发现', to: '/discovery' },
  { label: '热门', to: '/trending' },
  { label: '活动', to: '/books' },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const username = computed(() => authStore.user?.username || 'Writer')

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="sticky top-0 z-50 bg-bg-base/92 backdrop-blur border-b border-line-primary">
    <div class="mx-auto w-full max-w-[1440px] px-6 md:px-8 h-16 flex items-center justify-between gap-4 tech-header-frame">
      <RouterLink to="/" class="shrink-0 inline-flex items-center">
        <img :src="logoUrl" alt="Tree Story" class="h-8 w-auto" />
      </RouterLink>

      <nav class="hidden md:flex items-center gap-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'nav-link--active': isActive(item.to) }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="flex items-center gap-2">
        <template v-if="authStore.isLoggedIn">
          <RouterLink to="/notifications" class="text-text-muted text-sm hover:text-text-primary transition-colors">
            {{ username }}
          </RouterLink>
          <AppButton size="small" ghost accent="green" @click="handleLogout">退出</AppButton>
        </template>
        <template v-else>
          <RouterLink to="/login">
            <AppButton size="small" ghost accent="blue">登录</AppButton>
          </RouterLink>
          <RouterLink to="/register" class="hidden sm:inline-flex">
            <AppButton size="small" accent="violet">注册</AppButton>
          </RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.nav-link {
  position: relative;
  color: #a1a1aa;
  font-size: 0.875rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-decoration: none;
  border: 1px solid rgba(255, 255, 255, 0.16);
  padding: 0.35rem 0.7rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  transition: all 0.2s ease;
}

.nav-link::after {
  content: '';
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 6px;
  height: 6px;
  border-right: 1px solid rgba(255, 255, 255, 0.35);
  border-bottom: 1px solid rgba(255, 255, 255, 0.35);
  opacity: 0.45;
}

.nav-link:hover {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.45);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.nav-link--active {
  color: #ffffff;
  border-color: rgba(124, 58, 237, 0.72);
  box-shadow:
    inset 0 0 0 1px rgba(124, 58, 237, 0.42),
    0 0 14px rgba(124, 58, 237, 0.16);
}

.nav-link--active::after {
  border-right-color: rgba(124, 58, 237, 0.85);
  border-bottom-color: rgba(124, 58, 237, 0.85);
  opacity: 1;
}

.tech-header-frame {
  position: relative;
}

.tech-header-frame::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0), rgba(59, 130, 246, 0.48), rgba(124, 58, 237, 0));
}
</style>
