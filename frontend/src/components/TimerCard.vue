<script setup lang="ts">
/**
 * 倒计时大卡片 + 胶囊
 * 来源：docs/PRD.md §3.3.5 + docs/Design.md §3.8
 *
 * 形态：
 *  - 大卡片：固定浮层（顶栏下方），全圆角 + 主色渐变 + 大号倒计时数字
 *  - 胶囊：右上角小圆角，显示跳动数字 + 名称
 *  - 归零：全屏浮层 + 摇晃闹钟 + "知道了" 按钮
 *
 * 持久化：MVP 用 setInterval + Date.now 重算；不做 localStorage 跨会话
 *         （教程页本身在导航栈中，重进会重新挂载，简单起见先这样）
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

interface Props {
  name: string /* 倒计时名称（2-3 字） */
  totalSeconds: number /* 总秒数 */
  onDismissed?: () => void /* 用户点击"知道了"回调 */
}

const props = defineProps<Props>()

/* === 形态：'card' 大卡片，'pill' 胶囊 === */
type Mode = 'card' | 'pill' | 'finished'
const mode = ref<Mode>('card')

/* === 计时 === */
const endAt = ref<number>(Date.now() + props.totalSeconds * 1000)
const now = ref<number>(Date.now())

let timerId: number | null = null

const remainingMs = computed(() => Math.max(0, endAt.value - now.value))
const remainingSec = computed(() => Math.ceil(remainingMs.value / 1000))

const mm = computed(() =>
  String(Math.floor(remainingSec.value / 60)).padStart(2, '0'),
)
const ss = computed(() =>
  String(remainingSec.value % 60).padStart(2, '0'),
)

function tick() {
  now.value = Date.now()
  if (remainingMs.value <= 0) {
    mode.value = 'finished'
    if (timerId) {
      window.clearInterval(timerId)
      timerId = null
    }
  }
}

onMounted(() => {
  /* 3 秒后从大卡片缩到胶囊（Design §3.8） */
  window.setTimeout(() => {
    if (mode.value !== 'finished') mode.value = 'pill'
  }, 3000)
  timerId = window.setInterval(tick, 250)
})

onBeforeUnmount(() => {
  if (timerId) window.clearInterval(timerId)
})

/* === 形态切换：胶囊 → 大卡片 === */
function expandToCard() {
  mode.value = 'card'
}

/* === 关闭全屏提醒 === */
function onKnown() {
  props.onDismissed?.()
}
</script>

<template>
  <!-- 大卡片：固定浮层在顶栏下方 -->
  <Transition name="card">
    <div v-if="mode === 'card'" class="timer-card" role="status" aria-live="polite">
      <div class="timer-name">{{ name }}</div>
      <div class="timer-num">{{ mm }}:{{ ss }}</div>
    </div>
  </Transition>

  <!-- 胶囊：右上角，可点击回大卡片 -->
  <Transition name="pill">
    <button
      v-if="mode === 'pill'"
      class="timer-pill"
      type="button"
      aria-label="展开倒计时"
      @click="expandToCard"
    >
      <span class="pill-name">{{ name }}</span>
      <span class="pill-num">{{ mm }}:{{ ss }}</span>
    </button>
  </Transition>

  <!-- 归零：全屏浮层 -->
  <Transition name="fade">
    <div v-if="mode === 'finished'" class="timer-finished" role="dialog" aria-modal="true">
      <div class="finished-inner">
        <div class="alarm" aria-hidden="true">⏰</div>
        <div class="finished-name">{{ name }} 时间到</div>
        <button class="known-btn" type="button" @click="onKnown">知道了</button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* === 大卡片 === */
.timer-card {
  position: sticky;
  top: calc(var(--size-topbar) + var(--safe-top) + var(--size-progress));
  /* 叠在顶栏 + 进度条下方 */
  z-index: var(--z-overlay);
  margin: var(--space-4) var(--space-4) 0;
  /* 让卡片在页面里参与文档流，sticky 在顶部时吸住 */
  height: 120px;
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-xl);
  background: linear-gradient(
    135deg,
    var(--color-primary),
    var(--color-primary-light)
  );
  color: var(--color-text-inverse);
  box-shadow: var(--shadow-modal);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

.timer-name {
  font-size: var(--text-body); /* 18px */
  font-weight: var(--font-medium);
}

.timer-num {
  font-size: var(--text-display); /* 36px */
  font-weight: var(--font-bold);
  letter-spacing: 2px;
  font-variant-numeric: tabular-nums;
}

/* === 胶囊 === */
.timer-pill {
  position: fixed;
  top: calc(var(--size-topbar) + var(--safe-top) + var(--space-3));
  right: var(--space-4);
  z-index: var(--z-fixed);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-full);
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  box-shadow: var(--shadow-card);
  font-variant-numeric: tabular-nums;
}

.pill-name {
  font-size: var(--text-caption); /* 14px */
}

.pill-num {
  font-size: var(--text-body); /* 18px */
  font-weight: var(--font-bold);
}

/* === 归零全屏 === */
.timer-finished {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  background: var(--color-overlay-modal);
  display: flex;
  align-items: center;
  justify-content: center;
}

.finished-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
}

.alarm {
  font-size: 80px;
  line-height: 1;
  animation: shake 0.6s ease-in-out infinite;
}

@keyframes shake {
  0%, 100% { transform: rotate(0); }
  20% { transform: rotate(-12deg); }
  40% { transform: rotate(10deg); }
  60% { transform: rotate(-8deg); }
  80% { transform: rotate(6deg); }
}

.finished-name {
  font-size: var(--text-h2);
  color: var(--color-bg);
  font-weight: var(--font-medium);
}

.known-btn {
  width: 200px;
  height: 64px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
}

/* === 过渡动画 === */
.card-enter-active,
.card-leave-active,
.pill-enter-active,
.pill-leave-active,
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity var(--duration-normal) var(--ease-default),
    transform var(--duration-normal) var(--ease-default);
}

.card-enter-from,
.card-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.95);
}

.pill-enter-from,
.pill-leave-to {
  opacity: 0;
  transform: scale(0.7) translateY(-8px);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>