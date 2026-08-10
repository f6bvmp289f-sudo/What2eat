/**
 * 菜谱状态管理
 * 来源：docs/PRD.md §3.2-§3.5
 * MVP 阶段：用户数据走 localStorage（无登录）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import { useAuthStore } from './auth'

export interface DishImage {
  id: string
  url: string         // 本地预览 URL（blob:）
  file: File           // 原始文件
  status: 'pending' | 'uploading' | 'done' | 'failed'
  progress: number     // 0-100
}

export interface DishStep {
  index: number
  title: string
  description: string
  hasTimer?: boolean
  timerSeconds?: number
  substeps: string[]  // 详细子步骤（1.1/1.2/1.3 风格）
}

export interface Dish {
  id: string
  name: string
  description: string
  estimatedTime: string
  /** 菜品大图（白底高级白盘俯拍） */
  previewImage: string
  mainIngredients: string[]
  /** 口味描述，如"酸甜" */
  taste: string
  /** 烹饪方式，如"炒" */
  cookingMethod: string
  /** 难度，如"简单" */
  difficulty: string
  steps: DishStep[]
}

export interface DishScheme {
  id: string
  dishes: Dish[]
  carbRecommendation: { name: string; reason: string }
  createdAt: number
}

export interface Timer {
  id: string
  name: string         // 2-3 字
  endAt: number        // epoch ms（绝对结束时间，切后台不丢）
  startedAt: number
}

const STORAGE_KEYS = {
  HISTORY: 'kaifan:history',
  TIMER: 'kaifan:timer',
  PROGRESS: 'kaifan:progress',
}

export const useDishStore = defineStore('dish', () => {
  // === 状态 ===
  const uploadedImages = ref<DishImage[]>([])
  /** 用户在 Chat 输入的文字（传给后端 LLM） */
  const text = ref<string>('')
  /** 换一批模式：上一轮的菜名列表（传给后端去重） */
  const historyDishNames = ref<string[]>([])
  /** 换一批模式：用户已点"换一批"次数（最多 3 次） */
  const refreshCount = ref<number>(0)
  /** 换一批模式：最多可点几次 */
  const MAX_REFRESH_COUNT = 3
  const currentScheme = ref<DishScheme | null>(null)
  const isGenerating = ref(false)
  const history = ref<DishScheme[]>([])
  const timers = ref<Timer[]>([])
  const currentProgress = ref<{ dishId: string; stepIndex: number } | null>(null)

  // === 计算属性 ===
  const hasImages = computed(() => uploadedImages.value.length > 0)
  const allImagesUploaded = computed(() =>
    uploadedImages.value.length > 0 &&
    uploadedImages.value.every((img) => img.status === 'done'),
  )
  const activeTimerCount = computed(() => {
    const now = Date.now()
    return timers.value.filter((t) => t.endAt > now).length
  })

  // === 行为：图片 ===
  function addImages(files: File[]) {
    const newImages: DishImage[] = files.map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      url: URL.createObjectURL(file),
      file,
      status: 'pending',
      progress: 0,
    }))
    uploadedImages.value.push(...newImages)
    return newImages
  }

  function updateImageStatus(id: string, status: DishImage['status'], progress = 0) {
    const img = uploadedImages.value.find((i) => i.id === id)
    if (img) {
      img.status = status
      img.progress = progress
    }
  }

  function removeImage(id: string) {
    const idx = uploadedImages.value.findIndex((i) => i.id === id)
    if (idx > -1) {
      URL.revokeObjectURL(uploadedImages.value[idx].url)
      uploadedImages.value.splice(idx, 1)
    }
  }

  function clearImages() {
    uploadedImages.value.forEach((img) => URL.revokeObjectURL(img.url))
    uploadedImages.value = []
  }

  function setText(value: string) {
    text.value = value
  }

  function setHistoryDishNames(names: string[]) {
    historyDishNames.value = names
  }

  function incrementRefreshCount() {
    refreshCount.value += 1
  }

  function resetRefreshCount() {
    refreshCount.value = 0
    historyDishNames.value = []
  }

  // === 行为：菜谱方案 ===
  function setScheme(scheme: DishScheme) {
    currentScheme.value = scheme

    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      // 登录态：写到服务端 + 本地立即反映
      // 不写 localStorage（避免双源）
      const idx = history.value.findIndex((s) => s.id === scheme.id)
      if (idx > -1) {
        history.value[idx] = scheme
      } else {
        history.value.unshift(scheme)
        if (history.value.length > 50) history.value.pop()
      }
      // 异步写服务端，失败静默
      import('./history').then(({ useHistoryStore }) => {
        useHistoryStore().addRemote(scheme)
      })
      return
    }

    // 游客态：写 localStorage
    const idx = history.value.findIndex((s) => s.id === scheme.id)
    if (idx > -1) {
      history.value[idx] = scheme
    } else {
      history.value.unshift(scheme)
      if (history.value.length > 20) history.value.pop() // 最多 20 条
    }
    saveHistory()
  }

  /**
   * 登录态启动 / 登录成功后调用：
   * 拉服务端历史替换本地 history，并清掉 localStorage 旧数据（按 PRD 决策）
   */
  async function loadRemoteHistory(): Promise<void> {
    const { useHistoryStore } = await import('./history')
    const historyStore = useHistoryStore()
    await historyStore.fetchList()
    history.value = [...historyStore.remoteList]
    try {
      localStorage.removeItem(STORAGE_KEYS.HISTORY)
    } catch {
      // 忽略
    }
  }

  /** 退出登录时调用：清空历史（保留游客 localStorage 数据也清掉，避免与下次登录混淆） */
  function clearHistory(): void {
    history.value = []
    try {
      localStorage.removeItem(STORAGE_KEYS.HISTORY)
    } catch {
      // 忽略
    }
  }

  function removeSchemeFromHistory(schemeId: string): void {
    const idx = history.value.findIndex((s) => s.id === schemeId)
    if (idx > -1) {
      history.value.splice(idx, 1)
      // 登录态同步服务端
      const authStore = useAuthStore()
      if (authStore.isAuthenticated) {
        import('./history').then(({ useHistoryStore }) => {
          useHistoryStore().removeRemote(schemeId).catch((e) => {
            console.warn('删除历史失败', e)
          })
        })
      } else {
        saveHistory()
      }
    }
  }

  /** 从历史中加载某条到 currentScheme（点历史条目跳 Result 前调用） */
  function loadFromHistory(schemeId: string) {
    const scheme = history.value.find((s) => s.id === schemeId)
    if (scheme) currentScheme.value = scheme
  }

  function saveHistory() {
    try {
      // 只持久化必要字段，不存文件
      const light = history.value.map((s) => ({
        id: s.id,
        dishes: s.dishes.map((d) => ({
          id: d.id,
          name: d.name,
          description: d.description,
          estimatedTime: d.estimatedTime,
          previewImage: d.previewImage,
          mainIngredients: d.mainIngredients,
          steps: d.steps,
        })),
        carbRecommendation: s.carbRecommendation,
        createdAt: s.createdAt,
      }))
      localStorage.setItem(STORAGE_KEYS.HISTORY, JSON.stringify(light))
    } catch (e) {
      console.warn('保存历史记录失败', e)
    }
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.HISTORY)
      if (raw) history.value = JSON.parse(raw)
    } catch (e) {
      console.warn('加载历史记录失败', e)
    }
  }

  // === 行为：倒计时 ===
  function addTimer(name: string, seconds: number) {
    const timer: Timer = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name: name.slice(0, 3),
      endAt: Date.now() + seconds * 1000,
      startedAt: Date.now(),
    }
    timers.value.push(timer)
    saveTimers()
    return timer
  }

  function removeTimer(id: string) {
    const idx = timers.value.findIndex((t) => t.id === id)
    if (idx > -1) {
      timers.value.splice(idx, 1)
      saveTimers()
    }
  }

  function saveTimers() {
    try {
      localStorage.setItem(STORAGE_KEYS.TIMER, JSON.stringify(timers.value))
    } catch (e) {
      console.warn('保存倒计时失败', e)
    }
  }

  function loadTimers() {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.TIMER)
      if (raw) {
        const parsed: Timer[] = JSON.parse(raw)
        // 过滤已过期的
        const now = Date.now()
        timers.value = parsed.filter((t) => t.endAt > now)
      }
    } catch (e) {
      console.warn('加载倒计时失败', e)
    }
  }

  // === 行为：进度 ===
  function setProgress(dishId: string, stepIndex: number) {
    currentProgress.value = { dishId, stepIndex }
    try {
      localStorage.setItem(
        STORAGE_KEYS.PROGRESS,
        JSON.stringify(currentProgress.value),
      )
    } catch (e) {
      console.warn('保存进度失败', e)
    }
  }

  function loadProgress() {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.PROGRESS)
      if (raw) currentProgress.value = JSON.parse(raw)
    } catch (e) {
      console.warn('加载进度失败', e)
    }
  }

  return {
    // state
    uploadedImages,
    text,
    historyDishNames,
    refreshCount,
    MAX_REFRESH_COUNT,
    currentScheme,
    isGenerating,
    history,
    timers,
    currentProgress,
    // getters
    hasImages,
    allImagesUploaded,
    activeTimerCount,
    // actions
    addImages,
    updateImageStatus,
    removeImage,
    clearImages,
    setText,
    setHistoryDishNames,
    incrementRefreshCount,
    resetRefreshCount,
    setScheme,
    removeSchemeFromHistory,
    loadFromHistory,
    loadRemoteHistory,
    clearHistory,
    loadHistory,
    addTimer,
    removeTimer,
    loadTimers,
    setProgress,
    loadProgress,
  }
})
