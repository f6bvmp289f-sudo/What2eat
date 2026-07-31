/**
 * 路由配置
 * 来源：docs/PRD.md §2 核心用户旅程
 * 命名：所有页面路由用 kebab-case
 */
import { createRouter, createWebHistory } from 'vue-router'

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

export default router
