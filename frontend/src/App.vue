<script setup lang="ts">
import { onMounted } from 'vue'
import { useDishStore } from '@/stores/dish'

const dishStore = useDishStore()

onMounted(() => {
  // 启动时加载历史记录和倒计时
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
