<script setup lang="ts">
import { computed } from 'vue'
import { NAvatar, NBadge, NButton, NDropdown, NLayout, NLayoutFooter, NLayoutHeader, NSpace } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { useUnreadCountQuery } from '@/features/interaction/queries'
import { useAuthStore } from '@/stores/auth'
import { handleError } from '@/utils/error-handler'

type NavItem = {
  key: string
  label: string
  routeName?: string
  matchNames: string[]
}

type DropdownOption = {
  key: string
  label?: string
  type?: 'divider'
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { data: unreadCount } = useUnreadCountQuery()

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    {
      key: 'home',
      label: '首页',
      routeName: 'home',
      matchNames: ['home'],
    },
    {
      key: 'books',
      label: '故事册',
      routeName: 'books',
      matchNames: ['books', 'book-detail', 'story-node', 'story-lineage', 'story-write'],
    },
  ]

  if (authStore.isAdmin) {
    items.push({
      key: 'admin',
      label: '管理台',
      routeName: 'admin',
      matchNames: ['admin', 'admin-nodes', 'admin-books', 'admin-users'],
    })
  }

  return items
})

const currentSectionLabel = computed(() => {
  const matchedItem = navItems.value.find((item) => item.matchNames.includes(String(route.name)))
  return matchedItem?.label ?? '叙事终端'
})

const userDropdownOptions = computed<DropdownOption[]>(() => {
  const options: DropdownOption[] = [
    { label: '个人中心', key: 'profile' },
  ]

  if (authStore.isAdmin) {
    options.push({ label: '节点管理', key: 'admin-nodes' })
  }

  options.push({ type: 'divider', key: 'divider' })
  options.push({ label: '退出登录', key: 'logout' })
  return options
})

const mobileMenuOptions = computed<DropdownOption[]>(() => {
  const options: DropdownOption[] = navItems.value.map((item) => ({
    label: item.label,
    key: item.key,
  }))

  if (authStore.isAuthenticated) {
    options.push({ type: 'divider', key: 'divider-auth' })
    options.push({ label: '个人中心', key: 'profile' })
    options.push({ label: '通知中心', key: 'notifications' })
    if (authStore.isAdmin) {
      options.push({ label: '节点管理', key: 'admin-nodes' })
      options.push({ label: '管理台', key: 'admin' })
    }
    options.push({ type: 'divider', key: 'divider-logout' })
    options.push({ label: '退出登录', key: 'logout' })
  } else {
    options.push({ type: 'divider', key: 'divider-guest' })
    options.push({ label: '登录 / 注册', key: 'login' })
  }

  return options
})

const authRedirectTarget = computed(() => {
  if (route.name === 'login' || route.name === 'register' || route.name === 'auth-callback') {
    return '/books'
  }
  return route.fullPath || '/books'
})

const userInitial = computed(() => authStore.currentUser?.username?.charAt(0).toUpperCase() || 'U')
const userRoleLabel = computed(() => {
  if (authStore.isAdmin) return 'Admin'
  if (authStore.isWriter) return 'Writer'
  if (authStore.isBanned) return 'Banned'
  return 'Observer'
})
const unreadCountValue = computed(() => unreadCount.value?.unread_count ?? 0)

function isNavItemActive(item: NavItem) {
  return item.matchNames.includes(String(route.name))
}

async function handleSsoEntry() {
  try {
    await authStore.beginSsoLogin(authRedirectTarget.value)
  } catch (error) {
    handleError(error, '跳转 SSO 登录失败')
  }
}

function handleMenuAction(key: string) {
  const navItem = navItems.value.find((item) => item.key === key)
  if (navItem?.routeName) {
    void router.push({ name: navItem.routeName })
    return
  }

  if (key === 'logout') {
    authStore.logout()
    void router.push({ name: 'home' })
    return
  }

  if (key === 'login') {
    void handleSsoEntry()
    return
  }

  if (key === 'profile' || key === 'notifications' || key === 'admin' || key === 'admin-nodes') {
    void router.push({ name: key })
  }
}
</script>

<template>
  <n-layout class="app-shell">
    <div class="app-shell__backdrop ui-shell-grid" />

    <n-layout-header bordered class="app-header">
      <div class="app-header__inner">
        <RouterLink to="/" class="brand-mark">
          <span class="brand-mark__glyph">BF</span>
          <span class="brand-mark__text">
            <strong>分岔视界</strong>
            <small>Bifurcation Horizon</small>
          </span>
        </RouterLink>

        <div class="app-header__center">
          <p class="app-header__status">{{ currentSectionLabel }}</p>
          <nav class="app-nav" aria-label="主导航">
            <RouterLink
              v-for="item in navItems"
              :key="item.key"
              class="app-nav__link"
              :class="{ 'app-nav__link--active': isNavItemActive(item) }"
              :to="{ name: item.routeName }"
            >
              {{ item.label }}
            </RouterLink>
          </nav>
        </div>

        <div class="app-header__actions">
          <n-dropdown
            trigger="click"
            :options="mobileMenuOptions"
            placement="bottom-end"
            @select="handleMenuAction"
          >
            <n-button quaternary class="app-header__menu-trigger">
              菜单
            </n-button>
          </n-dropdown>

          <div v-if="authStore.isAuthenticated" class="app-user-zone">
            <RouterLink
              class="app-utility-link"
              :class="{ 'app-utility-link--active': route.name === 'notifications' }"
              :to="{ name: 'notifications' }"
            >
              <n-badge :value="unreadCountValue" :max="99" :show="unreadCountValue > 0">
                <span>通知</span>
              </n-badge>
            </RouterLink>

            <RouterLink
              v-if="authStore.isAdmin"
              class="app-utility-link"
              :class="{ 'app-utility-link--active': route.name === 'admin' }"
              :to="{ name: 'admin' }"
            >
              管理台
            </RouterLink>

            <RouterLink
              v-if="authStore.isAdmin"
              class="app-utility-link"
              :class="{ 'app-utility-link--active': route.name === 'admin-nodes' }"
              :to="{ name: 'admin-nodes' }"
            >
              节点
            </RouterLink>

            <n-dropdown
              trigger="click"
              :options="userDropdownOptions"
              placement="bottom-end"
              @select="handleMenuAction"
            >
              <button class="app-user-zone__trigger" type="button">
                <n-avatar
                  v-if="authStore.currentUser?.avatar"
                  :src="authStore.currentUser.avatar"
                  size="small"
                  class="app-user-zone__avatar"
                />
                <n-avatar v-else size="small" class="app-user-zone__avatar">
                  {{ userInitial }}
                </n-avatar>
                <span class="app-user-zone__identity">
                  <strong>
                    {{ authStore.currentUser?.username || '用户' }}
                    <span v-if="authStore.isAdmin" class="app-user-zone__role-chip">ADMIN</span>
                  </strong>
                  <small>{{ userRoleLabel }}</small>
                </span>
              </button>
            </n-dropdown>
          </div>

          <n-space v-else class="app-auth-entry">
            <n-button ghost class="app-auth-entry__button" @click="handleSsoEntry">
              登录
            </n-button>
            <n-button type="primary" class="app-auth-entry__button" @click="handleSsoEntry">
              注册
            </n-button>
          </n-space>
        </div>
      </div>
    </n-layout-header>

    <main class="app-main">
      <div class="app-main__inner">
        <router-view />
      </div>
    </main>

    <n-layout-footer bordered class="app-footer">
      <div class="app-footer__inner">
        <p>分岔视界 Bifurcation Horizon © 2026</p>
        <span>Worldline Observation Interface</span>
      </div>
    </n-layout-footer>
  </n-layout>
</template>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100vh;
  background: transparent;
  color: var(--text-primary);
}

.app-shell__backdrop {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.05), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 18%);
  pointer-events: none;
  z-index: 0;
}

.app-header,
.app-footer {
  position: relative;
  z-index: 1;
  background: rgba(6, 6, 6, 0.92);
  border-color: var(--line-soft);
  backdrop-filter: blur(10px);
}

.app-header {
  position: sticky;
  top: 0;
}

.app-header__inner,
.app-footer__inner,
.app-main__inner {
  width: min(1360px, calc(100% - 32px));
  margin: 0 auto;
}

.app-header__inner {
  min-height: 76px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  flex-shrink: 0;
}

.brand-mark__glyph {
  display: inline-grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.015));
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  font-family: var(--font-mono);
  font-size: 14px;
  letter-spacing: 0.18em;
  color: var(--text-primary);
}

.brand-mark__text {
  display: grid;
  gap: 2px;
}

.brand-mark__text strong {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.brand-mark__text small {
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.app-header__center {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.app-header__status {
  margin: 0;
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.app-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.app-nav__link,
.app-utility-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-secondary);
  font-size: 13px;
  letter-spacing: 0.08em;
  transition:
    border-color var(--transition-fast),
    color var(--transition-fast),
    background var(--transition-fast),
    box-shadow var(--transition-fast);
}

.app-nav__link:hover,
.app-utility-link:hover {
  border-color: var(--line-strong);
  color: var(--text-primary);
  box-shadow: var(--glow-focus);
}

.app-nav__link--active,
.app-utility-link--active {
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}

.app-header__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.app-header__menu-trigger {
  display: none;
  min-width: 74px;
  border: 1px solid var(--line-soft);
}

.app-user-zone,
.app-auth-entry {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-user-zone__trigger {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 6px 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-primary);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    background var(--transition-fast);
}

.app-user-zone__trigger:hover {
  border-color: var(--line-strong);
  box-shadow: var(--glow-focus);
  background: rgba(255, 255, 255, 0.04);
}

.app-user-zone__avatar {
  border: 1px solid var(--line-soft);
}

.app-user-zone__identity {
  display: grid;
  gap: 1px;
  text-align: left;
}

.app-user-zone__identity strong {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.app-user-zone__role-chip {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 0 6px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: var(--radius-xs);
  background: rgba(255, 255, 255, 0.08);
  color: var(--accent-bright);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.app-user-zone__identity small {
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.app-auth-entry__button {
  min-width: 88px;
}

.app-main {
  position: relative;
  z-index: 1;
  flex: 1;
  padding: 28px 0 48px;
}

.app-footer__inner {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  color: var(--text-faint);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

@media (max-width: 1120px) {
  .app-header__status {
    display: none;
  }

  .app-user-zone__identity {
    display: none;
  }
}

@media (max-width: 960px) {
  .app-header__inner {
    min-height: 70px;
  }

  .app-header__center {
    display: none;
  }

  .app-header__menu-trigger {
    display: inline-flex;
  }

  .brand-mark__text small {
    display: none;
  }

  .app-utility-link {
    display: none;
  }

  .app-auth-entry__button {
    min-width: 72px;
  }

  .app-footer__inner {
    flex-direction: column;
    justify-content: center;
    padding: 16px 0;
  }
}

@media (max-width: 640px) {
  .app-header__inner,
  .app-footer__inner,
  .app-main__inner {
    width: min(100%, calc(100% - 20px));
  }

  .brand-mark__text strong {
    font-size: 16px;
    letter-spacing: 0.1em;
  }

  .app-auth-entry {
    gap: 8px;
  }

  .app-auth-entry__button {
    min-width: 64px;
  }
}
</style>
