<script setup lang="ts">
/**
 * 收藏按钮（卡片右上角悬浮）
 * - 未登录态：点击跳登录（带 redirect）
 * - 登录态：调用 favoritesStore.toggle() 切收藏
 * - 阻止事件冒泡，不触发卡片点击
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import type { Dish } from '@/stores/dish'
import { useAuthStore } from '@/stores/auth'
import { useFavoritesStore } from '@/stores/favorites'

interface Props {
  dish: Dish
  schemeId: string
}

const props = defineProps<Props>()
const router = useRouter()
const auth = useAuthStore()
const favorites = useFavoritesStore()

const isFavorited = computed(() => favorites.isFavorited(props.dish.id))
const isSyncing = computed(() => favorites.syncing.has(props.dish.id))

async function onClick(e: Event) {
  e.stopPropagation()
  e.preventDefault()
  if (isSyncing.value) return

  if (!auth.isAuthenticated) {
    // 未登录跳登录，登录成功后跳回
    const redirect = router.currentRoute.value.fullPath
    router.push({ name: 'login', query: { redirect } })
    return
  }

  try {
    await favorites.toggle(props.dish, props.schemeId)
  } catch (err) {
    // api.ts 已经处理 401；其他错误给个简单提示
    console.warn('收藏操作失败', err)
    alert('收藏操作失败，请重试')
  }
}
</script>

<template>
  <button
    type="button"
    class="fav-btn"
    :class="{ active: isFavorited, syncing: isSyncing }"
    :aria-pressed="isFavorited"
    :aria-label="isFavorited ? '取消收藏' : '收藏'"
    @click="onClick"
  >
    <span class="icon" aria-hidden="true">{{ isFavorited ? '★' : '☆' }}</span>
  </button>
</template>

<style scoped>
.fav-btn {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-card);
  transition:
    transform var(--duration-fast) var(--ease-default),
    background-color var(--duration-fast) var(--ease-default);
}

.fav-btn:active {
  transform: scale(0.9);
}

.fav-btn.active {
  background: var(--color-primary-bg);
}

.icon {
  font-size: 18px;
  line-height: 1;
  color: var(--color-text-tertiary);
  transition: color var(--duration-fast) var(--ease-default);
}

.fav-btn.active .icon {
  color: var(--color-primary);
}

.fav-btn.syncing .icon {
  opacity: 0.5;
}
</style>