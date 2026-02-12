import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由元信息类型
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresAdmin?: boolean
    layout?: 'default' | 'auth' | 'admin'
  }
}

const routes: RouteRecordRaw[] = [
  // 首页
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/home/Index.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  // 认证相关
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      requiresAuth: false,
      layout: 'auth',
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: {
      requiresAuth: false,
      layout: 'auth',
    },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/auth/ForgotPassword.vue'),
    meta: {
      requiresAuth: false,
      layout: 'auth',
    },
  },
  // 发现页
  {
    path: '/discovery',
    name: 'Discovery',
    component: () => import('@/views/discovery/Index.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  {
    path: '/trending',
    name: 'Trending',
    component: () => import('@/views/discovery/Trending.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/discovery/Search.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  // 活动页
  {
    path: '/books',
    name: 'Books',
    component: () => import('@/views/books/Index.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  {
    path: '/books/:id',
    name: 'BookDetail',
    component: () => import('@/views/books/Detail.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  // 故事相关
  {
    path: '/story/node/:id',
    name: 'StoryNode',
    component: () => import('@/views/story/Read.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  {
    path: '/story/write',
    name: 'StoryWrite',
    component: () => import('@/views/story/Write.vue'),
    meta: {
      requiresAuth: true,
      layout: 'default',
    },
  },
  // 用户相关
  {
    path: '/user/:id',
    name: 'UserProfile',
    component: () => import('@/views/user/Profile.vue'),
    meta: {
      requiresAuth: false,
      layout: 'default',
    },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/user/Settings.vue'),
    meta: {
      requiresAuth: true,
      layout: 'default',
    },
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/notification/Index.vue'),
    meta: {
      requiresAuth: true,
      layout: 'default',
    },
  },
  // 管理员相关
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Index.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      layout: 'admin',
    },
  },
  {
    path: '/admin/audit',
    name: 'AdminAudit',
    component: () => import('@/views/admin/Audit.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      layout: 'admin',
    },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/admin/Users.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      layout: 'admin',
    },
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isLoggedIn = authStore.isLoggedIn
  const isAdmin = authStore.isAdmin

  // 检查是否需要登录
  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !isAdmin) {
    next({ name: 'Home' })
    return
  }

  // 如果已登录用户访问登录/注册页面，重定向到首页
  if ((to.name === 'Login' || to.name === 'Register') && isLoggedIn) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router