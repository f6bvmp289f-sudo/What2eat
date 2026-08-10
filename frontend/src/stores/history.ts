/**
 * 历史方案 store
 * - 已登录态：与服务端 /api/history 同步，作为权威来源
 * - 未登录态：所有方法直接 return，不影响使用（dishStore 仍走 localStorage）
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { apiFetch } from '@/lib/api'
import type { DishScheme } from './dish'

interface RemoteSchemeRow {
  id: string
  payload: DishScheme
  created_at: number
}

export const useHistoryStore = defineStore('history', () => {
  const remoteList = ref<DishScheme[]>([])
  const loading = ref(false)

  /** 拉服务端列表（登录态） */
  async function fetchList(): Promise<void> {
    loading.value = true
    try {
      const rows = await apiFetch<RemoteSchemeRow[]>('/api/history')
      // 按 created_at desc 服务端已经做了，直接取 payload
      remoteList.value = rows.map((r) => r.payload).filter((s) => s && s.id)
    } finally {
      loading.value = false
    }
  }

  /** 写入一条（登录态，失败静默不影响主流程） */
  async function addRemote(scheme: DishScheme): Promise<void> {
    try {
      await apiFetch('/api/history', {
        method: 'POST',
        body: {
          id: scheme.id,
          dishes: scheme.dishes,
          carbRecommendation: scheme.carbRecommendation,
          createdAt: scheme.createdAt,
        },
      })
      // 乐观更新本地列表（避免再发一次 GET）
      const idx = remoteList.value.findIndex((s) => s.id === scheme.id)
      if (idx > -1) {
        remoteList.value[idx] = scheme
      } else {
        remoteList.value.unshift(scheme)
      }
    } catch (e) {
      console.warn('写入历史失败（不影响主流程）', e)
    }
  }

  /** 删除一条（登录态） */
  async function removeRemote(schemeId: string): Promise<void> {
    await apiFetch(`/api/history/${encodeURIComponent(schemeId)}`, {
      method: 'DELETE',
    })
    remoteList.value = remoteList.value.filter((s) => s.id !== schemeId)
  }

  /** 清空远端列表（退出登录时） */
  function clearRemote() {
    remoteList.value = []
  }

  return {
    remoteList,
    loading,
    fetchList,
    addRemote,
    removeRemote,
    clearRemote,
  }
})