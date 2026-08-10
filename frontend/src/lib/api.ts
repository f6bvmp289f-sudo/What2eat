/**
 * 通用请求封装
 * - 自动 baseURL（dev 走 vite proxy，prod 同源）
 * - 自动加 Authorization: Bearer <token>
 * - 401 自动清 token 并跳 /login（带 redirect）
 * - 返回统一的 ApiError
 */

export class ApiError extends Error {
  status: number
  code?: string

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

/** 取得 token（独立函数，避免循环依赖） */
function getToken(): string | null {
  try {
    return localStorage.getItem('kaifan:auth_token')
  } catch {
    return null
  }
}

/** 触发 401 跳转（独立函数，避免循环依赖） */
function handleUnauthorized() {
  try {
    localStorage.removeItem('kaifan:auth_token')
  } catch {
    // 忽略
  }
  // 仅在当前不是登录页时才跳，避免循环
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    const redirect = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.href = `/login?redirect=${redirect}`
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: unknown
  /** 是否带 Authorization（默认 true） */
  withAuth?: boolean
  /** 是否自动处理 401 跳转（默认 true） */
  autoHandle401?: boolean
  signal?: AbortSignal
}

export async function apiFetch<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    withAuth = true,
    autoHandle401 = true,
    signal,
  } = opts

  const headers: Record<string, string> = {
    Accept: 'application/json',
  }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (withAuth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const resp = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  })

  // 204 No Content
  if (resp.status === 204) {
    return undefined as T
  }

  const text = await resp.text()
  let data: any = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      // 非 JSON 响应
      if (!resp.ok) {
        throw new ApiError(text || resp.statusText, resp.status)
      }
      return text as unknown as T
    }
  }

  if (!resp.ok) {
    // 401 单独处理
    if (resp.status === 401 && autoHandle401 && withAuth) {
      handleUnauthorized()
    }
    const message = data?.detail || data?.message || resp.statusText
    const code = data?.error?.code
    throw new ApiError(typeof message === 'string' ? message : '请求失败', resp.status, code)
  }

  return data as T
}

/** SSE 请求（不能用 fetch 自定义 header，改用 query 传 token） */
export function buildSseUrl(path: string): string {
  const token = getToken()
  if (!token) return path
  const sep = path.includes('?') ? '&' : '?'
  return `${path}${sep}access_token=${encodeURIComponent(token)}`
}

/** 强制重置 token 并跳登录（供 Pinia store 在异常时调用） */
export function forceLogoutAndRedirect(redirect?: string) {
  try {
    localStorage.removeItem('kaifan:auth_token')
  } catch {
    // 忽略
  }
  const r = redirect || (typeof window !== 'undefined' ? window.location.pathname : '/')
  window.location.href = `/login?redirect=${encodeURIComponent(r)}`
}