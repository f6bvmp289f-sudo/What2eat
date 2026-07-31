<script setup lang="ts">
/**
 * 教程步骤页（单步单屏）
 * 来源：docs/Design.md §4.6 + docs/PRD.md §3.3
 *
 * 结构：
 *   1. TopBar（z-sticky）：菜名
 *   2. ProgressBar（z-sticky）：N 节进度条
 *   3. step-header（序号 + 大标题 + 分割线）— 大标题 sticky 在进度条下方
 *   4. step-body（做法标签 + 当前步骤描述，可滚动）— 单步单屏
 *   5. bottom-bar（z-fixed）：上一步 / 下一步
 *
 * 切换步骤：横向滑动（从右滑入下一步 / 从左滑入上一步）
 * 滚动：大标题 36px → 28px 平滑缩小
 * 倒计时：当前步骤 hasTimer 时显示"开始倒计时 [N 秒]"按钮 → TimerCard
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
import TimerCard from '@/components/TimerCard.vue'
import { useDishStore, type Dish, type DishStep } from '@/stores/dish'

const route = useRoute()
const router = useRouter()
const dishStore = useDishStore()

/* === 当前 dish === */
const dishId = computed(() => String(route.params.dishId || ''))
const dish = computed<Dish | undefined>(() =>
  dishStore.currentScheme?.dishes.find((d) => d.id === dishId.value),
)
const totalSteps = computed(() => dish.value?.steps.length ?? 0)

/* === 当前步骤（从 localStorage 恢复） === */
const stepIndex = ref(0)
const initialized = ref(false)
function initStepIndex() {
  const progress = dishStore.currentProgress
  if (progress && progress.dishId === dishId.value) {
    stepIndex.value = Math.min(Math.max(0, progress.stepIndex), totalSteps.value - 1)
  } else {
    stepIndex.value = 0
  }
  initialized.value = true
}

/* === 滑动方向控制 === */
const transitionName = ref<'slide-from-left' | 'slide-from-right'>('slide-from-right')

/* === 当前步骤 === */
const currentStep = computed<DishStep | undefined>(() => dish.value?.steps[stepIndex.value])

/* === 倒计时 === */
const showTimer = ref(false)
function openTimer() { showTimer.value = true }

/* === 菜单（顶栏 ···） === */
const menuOpen = ref(false)
function toggleMenu() { menuOpen.value = !menuOpen.value }
function onRegenerateSteps() {
  menuOpen.value = false
  alert('重新生成步骤（待接 LLM）')
}
function onExit() {
  menuOpen.value = false
  router.push({ name: 'result' })
}

/* === 按钮 === */
const isFirst = computed(() => stepIndex.value === 0)
const isLast = computed(() => stepIndex.value === totalSteps.value - 1)

function onPrev() {
  if (isFirst.value) return
  /* 上一步：新内容从左边进来（从右滑出） */
  transitionName.value = 'slide-from-left'
  stepIndex.value -= 1
  dishStore.setProgress(dishId.value, stepIndex.value)
  window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
}

function onNext() {
  if (isLast.value) {
    router.push({ name: 'done', params: { dishId: dishId.value } })
    return
  }
  transitionName.value = 'slide-from-right'
  stepIndex.value += 1
  dishStore.setProgress(dishId.value, stepIndex.value)
  window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
}

onMounted(() => {
  if (!dish.value) {
    router.replace({ name: 'result' })
    return
  }
  initStepIndex()
})

onBeforeUnmount(() => {
  /* 无需清理：未注册 scroll 监听 */
})

/* === 进度条每节状态类 === */
function stepClass(idx: number): string {
  if (idx < stepIndex.value) return 'done'
  if (idx === stepIndex.value) return 'current'
  return 'todo'
}

/* === 步骤序号文字 === */
const cn = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
const stepNumberText = computed(() => {
  const idx = stepIndex.value + 1
  const total = totalSteps.value
  return `第${cn[idx] ?? idx}步 / 共${cn[total] ?? total}步`
})
</script>

<template>
  <div v-if="dish && initialized" class="tutorial page">
    <!-- 顶栏 -->
    <TopBar :title="dish.name" :show-back="true" back-to="result">
      <template #right>
        <button
          class="menu-trigger"
          type="button"
          aria-label="更多菜单"
          @click="toggleMenu"
        >
          <span aria-hidden="true">···</span>
        </button>
      </template>
    </TopBar>

    <!-- ··· 菜单浮层 -->
    <Transition name="fade">
      <div v-if="menuOpen" class="menu-overlay" @click="menuOpen = false">
        <ul class="menu-panel" @click.stop>
          <li>
            <button class="menu-item" type="button" @click="onRegenerateSteps">
              重新生成步骤
            </button>
          </li>
          <li>
            <button class="menu-item" type="button" @click="onExit">
              退出做菜
            </button>
          </li>
        </ul>
      </div>
    </Transition>

    <!-- 进度条 -->
    <div class="progress-bar">
      <span
        v-for="(_, idx) in dish.steps"
        :key="idx"
        class="progress-seg"
        :class="stepClass(idx)"
      />
    </div>

    <!-- 步骤序号 + 大标题（无分割线，无"做法"标签，简洁版） -->
    <header class="step-header">
      <p class="step-number">{{ stepNumberText }}</p>
      <Transition :name="transitionName" mode="out-in">
        <h2 :key="stepIndex" class="step-title">
          {{ currentStep?.title }}
        </h2>
      </Transition>
    </header>

    <!-- 步骤列表：单步单屏，只显示当前 stepIndex 的 substeps -->
    <main class="step-body">
      <Transition :name="transitionName" mode="out-in">
        <div :key="stepIndex" class="step-screen">
          <ol v-if="currentStep && currentStep.substeps && currentStep.substeps.length" class="substep-list">
            <li
              v-for="(sub, sidx) in currentStep.substeps"
              :key="sidx"
              class="substep-item"
            >
              <span class="substep-num">{{ sidx + 1 }}</span>
              <span class="substep-text">{{ sub }}</span>
            </li>
          </ol>

          <!-- 倒计时触发（仅当前步骤且 hasTimer 时显示） -->
          <div
            v-if="currentStep && currentStep.hasTimer && !showTimer"
            class="timer-trigger"
          >
            <button class="timer-btn" type="button" @click="openTimer">
              开始倒计时 {{ currentStep.timerSeconds }} 秒
            </button>
          </div>
        </div>
      </Transition>
    </main>

    <!-- 倒计时组件 -->
    <TimerCard
      v-if="showTimer && currentStep?.hasTimer && currentStep.timerSeconds"
      :name="currentStep.title.slice(0, 3)"
      :total-seconds="currentStep.timerSeconds"
      @dismissed="showTimer = false"
    />

    <!-- 底部按钮 -->
    <footer class="bottom-bar">
      <button
        class="btn btn-secondary"
        type="button"
        :disabled="isFirst"
        @click="onPrev"
      >
        上一步
      </button>
      <button
        class="btn btn-primary"
        type="button"
        @click="onNext"
      >
        {{ isLast ? '完成' : '下一步 →' }}
      </button>
    </footer>
  </div>
</template>

<style scoped>
.tutorial {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-bg);
  /* 让底部按钮不遮挡最后内容 */
  padding-bottom: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-8));
}

/* === 顶栏右侧菜单触发 === */
.menu-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--size-topbar);
  height: var(--size-topbar);
  font-size: 24px;
  line-height: 1;
  color: var(--color-text-primary);
  letter-spacing: 2px;
}

.menu-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-overlay);
  background: rgba(0, 0, 0, 0.2);
}

.menu-panel {
  position: absolute;
  top: calc(var(--size-topbar) + var(--safe-top) + 4px);
  right: var(--space-3);
  min-width: 160px;
  padding: var(--space-2) 0;
  background: var(--color-bg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-modal);
  list-style: none;
}

.menu-item {
  display: block;
  width: 100%;
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-size: var(--text-body);
  color: var(--color-text-primary);
}

.menu-item:active {
  background: var(--color-bg-secondary);
}

/* === 进度条 === */
.progress-bar {
  position: sticky;
  top: calc(var(--size-topbar) + var(--safe-top));
  z-index: var(--z-sticky);
  display: flex;
  height: var(--size-progress); /* 6px */
  background: var(--color-bg-tertiary);
}

.progress-seg {
  flex: 1;
  height: 100%;
}

.progress-seg + .progress-seg {
  border-left: 1px solid var(--color-bg); /* 1px 白色间隔 */
}

.progress-seg.done {
  background: var(--color-primary-bg); /* 浅橙 */
}

.progress-seg.current {
  background: var(--color-primary); /* 亮橙 */
}

.progress-seg.todo {
  background: var(--color-bg-tertiary); /* 灰 */
}

/* === 步骤序号 + 大标题 === */
.step-header {
  padding: var(--space-6) var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-divider); /* 标题与正文之间的分割线 */
}

.step-number {
  font-size: var(--text-caption); /* 14px，浅灰小字 */
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-4); /* 距大标题 16px */
}

.step-title {
  font-size: 52px; /* 超大粗体 */
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  line-height: 1.15;
  letter-spacing: -1px; /* 大字号下收紧字距 */
  margin: 0;
}

/* === 步骤列表（全部展示，大字号描述 + 宽松留白） === */
.step-body {
  padding: var(--space-6) var(--space-5);
  flex: 1;
}

.step-list {
  list-style: none;
}

.step-item {
  position: relative;
  display: grid;
  grid-template-columns: 36px 1fr;
  column-gap: var(--space-5); /* 序号与描述间距加大 */
  padding-bottom: var(--space-8); /* 步骤之间加大间距 */
}

/* 圆形序号：精致灰色背景 */
.step-num {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--color-bg-tertiary); /* 灰 */
  color: var(--color-text-secondary);
  font-size: var(--text-body-sm); /* 16px */
  font-weight: var(--font-medium);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 中间连接虚线：width 0 + border-left dashed，最直接的虚线做法 */
.step-line {
  position: absolute;
  left: 17px; /* 圆形序号中心 (36/2 - 1) */
  top: 36px; /* 从圆形序号底部开始 */
  bottom: calc(-1 * var(--space-8)); /* 跨越到下一个 item 顶部 */
  width: 0;
  border-left: 2px dashed var(--color-text-tertiary);
}

.step-desc {
  font-size: 28px; /* 比之前 30 略小 */
  color: var(--color-text-primary);
  line-height: 1.65;
}

/* === 步骤屏（单步单屏：只显示当前步骤的 substeps） === */
.step-screen {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

/* === 子步骤列表（1/2/3 编号 + 虚线连接 + 文本） === */
.substep-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-6); /* 子步骤之间 24px 间隔 */
}

.substep-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  font-size: 26px;
  color: var(--color-text-primary);
  line-height: 1.6;
  /* 容器留出虚线空间（最后一项除外） */
}

/* 虚线连接：在圆形下方延伸，最后一项隐藏 */
.substep-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 15px; /* 圆形中心 (32/2 - 1) */
  top: 36px; /* 圆形底边 + 2px */
  width: 1px;
  height: calc(var(--space-6) + 8px); /* 跨越 gap 到底部 */
  border-left: 1px dashed var(--color-border-strong);
}

.substep-num {
  flex: 0 0 32px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary); /* 灰底（按用户图） */
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: var(--font-medium);
  border-radius: var(--radius-full);
  flex-shrink: 0;
  /* 圆形下方 z-index 比虚线高，避免虚线穿过圆形 */
  position: relative;
  z-index: 1;
}

.substep-text {
  flex: 1;
  padding-top: 2px;
}

.timer-trigger {
  margin-top: var(--space-4);
  grid-column: 2;
}

.timer-btn {
  height: var(--size-button); /* 48px */
  padding: 0 var(--space-5);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  background: var(--color-primary-bg);
  color: var(--color-text-primary);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  transition: opacity var(--duration-fast) var(--ease-default);
}

.timer-btn:active {
  opacity: 0.85;
}

/* === 底部按钮 === */
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-fixed);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-3));
  padding: 0 var(--space-4);
  padding-bottom: calc(var(--safe-bottom) + var(--space-3));
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
}

.btn {
  height: var(--size-button-lg); /* 56px */
  padding: 0 var(--space-6);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.btn-secondary {
  flex: 0 0 30%;
  background: var(--color-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-primary {
  flex: 1;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
}

/* === 步骤切换：横向滑动 === */
.slide-from-right-enter-active,
.slide-from-right-leave-active,
.slide-from-left-enter-active,
.slide-from-left-leave-active {
  transition:
    transform var(--duration-normal) var(--ease-default),
    opacity var(--duration-normal) var(--ease-default);
}

/* 下一步：从右滑入 */
.slide-from-right-enter-from {
  transform: translateX(30%);
  opacity: 0;
}
.slide-from-right-leave-to {
  transform: translateX(-30%);
  opacity: 0;
}

/* 上一步：从左滑入 */
.slide-from-left-enter-from {
  transform: translateX(-30%);
  opacity: 0;
}
.slide-from-left-leave-to {
  transform: translateX(30%);
  opacity: 0;
}

/* === 菜单淡入淡出 === */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-default);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>