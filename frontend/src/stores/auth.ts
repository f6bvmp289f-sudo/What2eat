/**
 * 鉴权状态
 * - token 存 localStorage['kaifan:auth_token']
 * - 启动时 restoreFromStorage() 从 localStorage 恢复 token + 拉一次 /me
 * - login/register 成功后写入 token 并 fetchMe
 * - logout 清 token + 清状态
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError, apiFetch } from '@/lib/api'

const TOKEN_KEY = 'kaifan:auth_token'

export interface AuthUser {
  id: number
  username: string
  created_at: number
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<AuthUser | null>(null)
  const loading = ref(false)
  const restoring = ref(true) // 启动恢复阶段

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  /** 从 localStorage 恢复 token，并拉一次 /me 验证有效性 */
  async function restoreFromStorage(): Promise<void> {
    restoring.value = true
    try {
      const t = localStorage.getItem(TOKEN_KEY)
      if (t) {
        token.value = t
        try {
          await fetchMe()
        } catch (e) {
          // /me 失败（401/网络）→ 清掉 token 视为未登录
          if (e instanceof ApiError && e.status === 401) {
            clearAuth()
          }
          // 其他错误保留 token，下次访问再校验
        }
      }
    } finally {
      restoring.value = false
    }
  }

  async function fetchMe(): Promise<void> {
    const me = await apiFetch<AuthUser>('/api/auth/me')
    user.value = me
  }

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    try {
      const data = await apiFetch<{ token: string; user: AuthUser }>(
        '/api/auth/login',
        {
          method: 'POST',
          body: { username, password },
          withAuth: false,
          autoHandle401: false,
        },
      )
      applyAuth(data.token, data.user)
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, password: string): Promise<void> {
    loading.value = true
    try {
      const data = await apiFetch<{ token: string; user: AuthUser }>(
        '/api/auth/register',
        {
          method: 'POST',
          body: { username, password },
          withAuth: false,
          autoHandle401: false,
        },
      )
      applyAuth(data.token, data.user)
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    clearAuth()
  }

  function applyAuth(t: string, u: AuthUser) {
    token.value = t
    user.value = u
    try {
      localStorage.setItem(TOKEN_KEY, t)
    } catch {
      // localStorage 不可用（隐私模式等），忽略
    }
  }

  function clearAuth() {
    token.value = null
    user.value = null
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      // 忽略
    }
  }

  return {
    // state
    token,
    user,
    loading,
    restoring,
    // getters
    isAuthenticated,
    // actions
    restoreFromStorage,
    fetchMe,
    login,
    register,
    logout,
  }
})