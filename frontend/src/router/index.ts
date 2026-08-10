/**
 * 路由配置
 * 来源：docs/PRD.md §2 核心用户旅程
 * 命名：所有页面路由用 kebab-case
 */
import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
      meta: { title: '开饭' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录', hideTabBar: true, guestOnly: true },
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('@/views/Upload.vue'),
      meta: { title: '已上传图片' },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/Chat.vue'),
      meta: { title: '和开饭聊聊' },
    },
    {
      path: '/loading',
      name: 'loading',
      component: () => import('@/views/Loading.vue'),
      meta: { title: '菜谱生成中' },
    },
    {
      path: '/result',
      name: 'result',
      component: () => import('@/views/Result.vue'),
      meta: { title: '推荐菜谱' },
    },
    {
      path: '/tutorial/:dishId',
      name: 'tutorial',
      component: () => import('@/views/Tutorial.vue'),
      meta: { title: '做菜' },
    },
    {
      path: '/dish/:dishId',
      name: 'dish-detail',
      component: () => import('@/views/DishDetail.vue'),
      meta: { title: '菜品详情' },
    },
    {
      path: '/done/:dishId',
      name: 'done',
      component: () => import('@/views/Done.vue'),
      meta: { title: '完成了' },
    },
    // ===== 我的 =====
    {
      path: '/mine',
      name: 'mine',
      component: () => import('@/views/Mine.vue'),
      meta: { title: '我的', requiresAuth: true },
    },
    {
      path: '/mine/history',
      name: 'mine-history',
      component: () => import('@/views/History.vue'),
      meta: { title: '历史记录', requiresAuth: true },
    },
    {
      path: '/mine/favorites',
      name: 'mine-favorites',
      component: () => import('@/views/Favorites.vue'),
      meta: { title: '我的收藏', requiresAuth: true },
    },
  ],
  // 每次路由切换回到顶部
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  if (to.meta?.title) {
    document.title = `${to.meta.title} · 开饭`
  }
})

// ===== 守卫：访问 requiresAuth 路由时检查登录 =====
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 启动期等待 token 恢复
  if (auth.restoring) {
    await auth.restoreFromStorage()
  }

  // 需要登录：未登录 → 跳登录（带 redirect）
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  // 仅游客可访问（如 /login）：已登录 → 跳 redirect 或 /mine
  if (to.meta.guestOnly && auth.isAuthenticated) {
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/mine'
    return redirect
  }

  return true
})

export default router