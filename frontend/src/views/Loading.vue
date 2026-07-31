<script setup lang="ts">
/**
 * 菜谱生成加载态（简化版）
 * 来源：用户反馈（2026-07-30）—— 不需要 SSE 实时进度，只显示"开饭正在思考中"
 *
 * 流程：
 *   1. 三个食材图标循环切换（thinking 状态）
 *   2. 后端 SSE done 事件到达 → 启动落停动画（三个图标依次变同一个）
 *   3. 落停完成（约 2.4s）→ router.push('result')
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  pickRandomIngredient,
  type Ingredient,
} from '@/assets/ingredients'
import { useDishStore, type DishScheme } from '@/stores/dish'

const router = useRouter()
const dishStore = useDishStore()

/* === 阶段 === */
type Phase = 'thinking' | 'landing'
const phase = ref<Phase>('thinking')

/* === 错误 === */
interface ErrorState {
  code: string
  message: string
}
const error = ref<ErrorState | null>(null)

/* === 食材图标（裸图，竖排） === */
const slots = ref<Ingredient[]>([
  pickRandomIngredient(),
  pickRandomIngredient(),
  pickRandomIngredient(),
])

/* 落停后的"最终食材"（从三个里随机选一个，模拟"三选一"） */
const finalPick = ref<Ingredient>(pickRandomIngredient())

const timers: ReturnType<typeof setInterval | typeof setTimeout>[] = []

/* === Thinking 阶段：三个图标每 800ms 切换一次（错开） === */
function startThinkingCycle() {
  for (let i = 0; i < 3; i++) {
    const t = setInterval(() => {
      if (phase.value !== 'thinking') {
        clearInterval(t)
        return
      }
      slots.value[i] = pickRandomIngredient()
    }, 800 + i * 150)
    timers.push(t)
  }
}

/* === 退出 === */
function onExit() {
  abort()
  router.push({ name: 'home' })
}

/* === 跳回 Chat 重新上传 === */
function onBackToChat() {
  abort()
  router.push({ name: 'chat' })
}

/* === File → base64 data URI === */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/* === SSE 请求 === */
let abortController: AbortController | null = null

function abort() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

function parseSSE(buffer: string): { events: Array<{ event: string; data: any }>; rest: string } {
  const events: Array<{ event: string; data: any }> = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() || ''
  for (const block of parts) {
    if (!block.trim() || block.startsWith(':')) continue
    let eventName = 'message'
    const dataLines: string[] = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) {
        eventName = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        dataLines.push(line.slice(6))
      }
    }
    if (dataLines.length > 0) {
      try {
        events.push({ event: eventName, data: JSON.parse(dataLines.join('\n')) })
      } catch {
        /* ignore malformed */
      }
    }
  }
  return { events, rest }
}

async function callBackend() {
  abort()

  // 1. 图片转 base64
  const imagesB64: string[] = []
  for (const img of dishStore.uploadedImages) {
    imagesB64.push(await fileToBase64(img.file))
  }

  abortController = new AbortController()
  let response: Response
  try {
    response = await fetch('/api/generate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        images: imagesB64,
        text: dishStore.text,
        history_dish_names: dishStore.historyDishNames,
      }),
      signal: abortController.signal,
    })
  } catch (e: any) {
    if (e?.name === 'AbortError') return
    error.value = { code: 'NETWORK_ERROR', message: '网络异常，请检查后端是否启动' }
    return
  }

  if (!response.ok || !response.body) {
    error.value = { code: 'HTTP_ERROR', message: `服务异常 (${response.status})` }
    return
  }

  // 2. 读 SSE 流（只关心 done 和 error，其他事件忽略）
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const { events, rest } = parseSSE(buffer)
      buffer = rest

      for (const { event, data } of events) {
        if (event === 'done') {
          const scheme = data.scheme as DishScheme
          dishStore.setScheme(scheme)
          // 不立即跳！先启动落停动画
          startLanding()
          return
        }
        if (event === 'error') {
          error.value = { code: data.code || 'UNKNOWN', message: data.message || 'AI 处理失败' }
          return
        }
        // 其他 progress 事件：忽略（不显示阶段）
      }
    }
  } catch (e: any) {
    if (e?.name === 'AbortError') return
    console.error('SSE read error:', e)
    error.value = { code: 'STREAM_ERROR', message: '数据流中断，请重试' }
  }
}

/* === Landing 阶段：三个图标依次落停成 finalPick === */
function startLanding() {
  phase.value = 'landing'

  // 三个图标依次变成 finalPick（每个 600ms 间隔）
  slots.value.forEach((_, i) => {
    const t = setTimeout(() => {
      slots.value[i] = finalPick.value
    }, i * 600)
    timers.push(t)
  })

  // 三个全部落停完成后（600 + 600*3 = 2.4s）再跳 Result
  const jump = setTimeout(() => {
    router.push({ name: 'result' })
  }, 600 + 600 * 3)
  timers.push(jump)
}

onMounted(() => {
  // 防御：store 没数据 → 回 Chat
  if (dishStore.uploadedImages.length === 0 && !dishStore.text.trim()) {
    router.replace({ name: 'chat' })
    return
  }
  startThinkingCycle()
  callBackend()
})

onBeforeUnmount(() => {
  abort()
  timers.forEach((t) => clearTimeout(t))
  timers.forEach((t) => clearInterval(t))
})
</script>

<template>
  <div class="loading page">
    <!-- 透明顶部：仅退出按钮 -->
    <header class="loading-header">
      <button
        class="exit-btn"
        type="button"
        aria-label="退出"
        @click="onExit"
      >
        <span aria-hidden="true">‹</span>
      </button>
    </header>

    <main class="loading-main">
      <!-- 三个食材图标（竖排；thinking 循环 / landing 落停） -->
      <div class="ingredients" :class="{ landing: phase === 'landing' }">
        <div
          v-for="(ing, idx) in slots"
          :key="idx"
          class="ingredient"
          :class="{ landed: phase === 'landing' }"
        >
          <img
            class="ingredient-img"
            :src="ing.url"
            :alt="ing.name"
            loading="eager"
          />
        </div>
      </div>

      <!-- 错误 UI -->
      <div v-if="error" class="status-block error">
        <p class="status-title">哎呀，出了点问题</p>
        <p class="status-msg">{{ error.message }}</p>
        <button class="status-btn" type="button" @click="onBackToChat">
          重新上传
        </button>
      </div>

      <!-- 统一文案：开饭正在思考中 -->
      <p v-else class="status-msg">开饭正在思考中</p>
    </main>
  </div>
</template>

<style scoped>
.loading {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-bg);
}

/* === 透明顶部 === */
.loading-header {
  position: absolute;
  top: var(--safe-top);
  left: 0;
  z-index: var(--z-sticky);
  padding: var(--space-2) var(--space-3);
}

.exit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--size-topbar);
  height: var(--size-topbar);
  background: transparent;
  color: var(--color-text-primary);
  font-size: 28px;
  line-height: 1;
  border-radius: var(--radius-md);
  transition: opacity var(--duration-fast) var(--ease-default);
}

.exit-btn:active {
  opacity: 0.6;
}

/* === 主内容 === */
.loading-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-4) var(--space-4);
  padding-top: calc(var(--safe-top) + var(--size-topbar) + var(--space-6));
  gap: var(--space-10);
}

/* === 食材图标（裸图，竖排） === */
.ingredients {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
}

.ingredient {
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* thinking 阶段：每个图标轻微缩放呼吸 */
  animation: pulse 800ms var(--ease-default) infinite alternate;
}

.ingredients.landing .ingredient {
  /* landing 阶段：停止呼吸 */
  animation: none;
}

.ingredient:nth-child(2) { animation-delay: 100ms; }
.ingredient:nth-child(3) { animation-delay: 200ms; }

.ingredient-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-md);
  display: block;
  /* 落停时弹性放大 */
  transition: transform 600ms var(--ease-emphasis);
}

.ingredient.landed .ingredient-img {
  animation: pop 600ms var(--ease-emphasis);
}

@keyframes pulse {
  from { transform: scale(1); }
  to   { transform: scale(0.94); }
}

@keyframes pop {
  0%   { transform: scale(1); }
  50%  { transform: scale(1.15); }
  100% { transform: scale(1); }
}

/* === 文案 === */
.status-msg {
  font-size: var(--text-body); /* 18px */
  color: var(--color-text-secondary);
  text-align: center;
  margin: 0;
}

/* === 错误态 === */
.status-block.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

.status-title {
  font-size: var(--text-h3);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.status-btn {
  margin-top: var(--space-2);
  height: 44px;
  padding: 0 var(--space-8);
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  font-size: var(--text-body-sm);
  font-weight: var(--font-medium);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.status-btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}
</style>
