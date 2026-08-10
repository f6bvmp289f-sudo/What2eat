<script setup lang="ts">
import { onMounted } from 'vue'
import { useDishStore } from '@/stores/dish'
import { useAuthStore } from '@/stores/auth'

const dishStore = useDishStore()
const authStore = useAuthStore()

onMounted(async () => {
  // 1. 恢复登录态（恢复失败则视为未登录，不抛错）
  await authStore.restoreFromStorage()

  // 2. 加载菜谱相关本地数据（历史/倒计时/进度）
  dishStore.loadHistory()
  dishStore.loadTimers()
  dishStore.loadProgress()
})
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style>
/* === 页面切换动画：横向滑动 === */
.page-enter-active,
.page-leave-active {
  transition:
    transform var(--duration-normal) var(--ease-default),
    opacity var(--duration-normal) var(--ease-default);
}

.page-enter-from {
  transform: translateX(30%);
  opacity: 0;
}

.page-leave-to {
  transform: translateX(-30%);
  opacity: 0;
}
</style>
