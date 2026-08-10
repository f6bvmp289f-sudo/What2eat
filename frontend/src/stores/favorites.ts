/**
 * 收藏 store
 * - 已登录态：与服务端 /api/favorites 同步
 * - 未登录态：所有方法提示并跳登录（不静默失败）
 *
 * 注意：当前 scheme 由调用方传入（用于追溯来源）
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { apiFetch } from '@/lib/api'
import type { Dish } from './dish'

interface FavoriteRow {
  id: number
  scheme_id: string
  dish_id: string
  dish_payload: Dish
  created_at: number
}

export const useFavoritesStore = defineStore('favorites', () => {
  const list = ref<FavoriteRow[]>([])
  const loading = ref(false)
  const syncing = ref<Set<string>>(new Set()) // 正在同步的 dish_id

  /** 方便按 dish_id 快速判断 */
  const favoriteIds = computed<Set<string>>(() => new Set(list.value.map((f) => f.dish_id)))

  function isFavorited(dishId: string): boolean {
    return favoriteIds.value.has(dishId)
  }

  async function fetchList(): Promise<void> {
    loading.value = true
    try {
      list.value = await apiFetch<FavoriteRow[]>('/api/favorites')
    } finally {
      loading.value = false
    }
  }

  /**
   * 切换收藏状态
   * - 未收藏 → 收藏
   * - 已收藏 → 取消收藏
   * 返回最终的收藏状态（true = 已收藏）
   */
  async function toggle(dish: Dish, schemeId: string): Promise<boolean> {
    const id = dish.id
    syncing.value.add(id)
    try {
      if (isFavorited(id)) {
        await apiFetch(`/api/favorites/${encodeURIComponent(id)}`, {
          method: 'DELETE',
        })
        list.value = list.value.filter((f) => f.dish_id !== id)
        return false
      } else {
        const created = await apiFetch<FavoriteRow>('/api/favorites', {
          method: 'POST',
          body: {
            scheme_id: schemeId,
            dish_id: id,
            dish_payload: dish,
          },
        })
        list.value.unshift(created)
        return true
      }
    } finally {
      syncing.value.delete(id)
    }
  }

  function clearFavorites() {
    list.value = []
  }

  return {
    list,
    loading,
    syncing,
    favoriteIds,
    isFavorited,
    fetchList,
    toggle,
    clearFavorites,
  }
})