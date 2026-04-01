import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由配置
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/pages/home/HomePage.vue'),
    },
    {
      path: '/books',
      name: 'books',
      component: () => import('@/pages/books/BookListPage.vue'),
    },
    {
      path: '/books/:bookId',
      name: 'book-detail',
      component: () => import('@/pages/books/BookDetailPage.vue'),
    },
    {
      path: '/story/node/:nodeId',
      name: 'story-node',
      component: () => import('@/pages/story/StoryNodePage.vue'),
    },
    {
      path: '/story/lineage/:nodeId',
      name: 'story-lineage',
      component: () => import('@/pages/story/StoryLineagePage.vue'),
    },
    {
      path: '/story/write/:bookId',
      name: 'story-write',
      component: () => import('@/pages/story/StoryWritePage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/auth/LoginPage.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/pages/auth/RegisterPage.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('@/pages/auth/AuthCallbackPage.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/pages/user/ProfilePage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/pages/notification/NotificationPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/pages/admin/AdminDashboardPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/pending',
      name: 'admin-pending',
      component: () => import('@/pages/admin/AdminPendingNodesPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/books',
      name: 'admin-books',
      component: () => import('@/pages/admin/AdminBooksPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/pages/admin/AdminUsersPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('@/pages/misc/ForbiddenPage.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/pages/misc/NotFoundPage.vue'),
    },
  ],
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要登录
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  // 检查是否仅允许访客访问（已登录用户访问登录/注册页会跳转）
  if (to.meta.guestOnly && authStore.isAuthenticated) {
    next({ name: 'home' })
    return
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'forbidden' })
    return
  }
  
  next()
})

export default router
