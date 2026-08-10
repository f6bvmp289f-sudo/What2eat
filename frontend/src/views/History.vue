<script setup lang="ts">
/**
 * 历史记录列表（已登录态）
 * 视觉：时间轴（左侧圆点 + 连接线）+ 分组卡片
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BottomTab from '@/components/BottomTab.vue'
import DishCard from '@/components/DishCard.vue'
import Icon from '@/components/Icon.vue'
import TopBar from '@/components/TopBar.vue'
import type { Dish, DishScheme } from '@/stores/dish'
import { useDishStore } from '@/stores/dish'
import { useAuthStore } from '@/stores/auth'

// 历史记录背景图
import historyBg from '@/assets/history-bg.png'

const router = useRouter()
const dishStore = useDishStore()
const auth = useAuthStore()

const items = computed<DishScheme[]>(() => dishStore.history)
const isEmpty = computed(() => items.value.length === 0)

onMounted(async () => {
  if (auth.isAuthenticated) {
    try {
      await dishStore.loadRemoteHistory()
    } catch (e) {
      console.warn('拉取历史失败', e)
    }
  }
})

function onDishClick(dish: Dish) {
  const scheme = items.value.find((s) => s.dishes.some((d) => d.id === dish.id))
  if (!scheme) return
  dishStore.loadFromHistory(scheme.id)
  router.push({ name: 'result' })
}

// 删除 sheet
const showDelete = ref(false)
const deleteTarget = ref<string | null>(null)

function openDelete(schemeId: string, e: Event) {
  e.stopPropagation()
  deleteTarget.value = schemeId
  showDelete.value = true
}

function closeDelete() {
  showDelete.value = false
  deleteTarget.value = null
}

function confirmDelete() {
  if (deleteTarget.value) {
    dishStore.removeSchemeFromHistory(deleteTarget.value)
  }
  closeDelete()
}

// ===== 时间格式化（按 PRD 友好的"刚刚/今天/昨天/更早"分级） =====

function formatDate(ts: number) {
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (d.toDateString() === now.toDateString()) {
    return `今天 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
  const yest = new Date(now.getTime() - 86400_000)
  if (d.toDateString() === yest.toDateString()) {
    return `昨天 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
  // 更早：只显示"X 月 X 日"
  return `${d.getMonth() + 1} 月 ${d.getDate()} 日`
}

/** 用于时间轴 dot 颜色 — 越新鲜越暖 */
function dotClass(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 3600_000) return 'dot-hot' // 一小时内
  if (d.toDateString() === now.toDateString()) return 'dot-warm' // 今天
  return 'dot-cool' // 更早
}
</script>

<template>
  <div
    class="history page"
    :style="{
      backgroundImage: `url(${historyBg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center -80px',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'scroll',
    }"
  >
    <!-- 背景图上的极淡暖色氛围 -->
    <div class="bg" aria-hidden="true" />

    <TopBar title="历史记录" back-to="mine" />

    <main class="content">
      <!-- 空状态 -->
      <div v-if="isEmpty" class="empty">
        <div class="empty-icon" aria-hidden="true">
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="40" r="36" fill="#FFF1EA" />
            <path
              d="M22 42h36 a14 14 0 0 1-28 0 a14 14 0 0 1 28 0 M40 22 v6"
              stroke="#FF7A45"
              stroke-width="2"
              stroke-linecap="round"
              fill="none"
            />
            <circle cx="34" cy="36" r="2" fill="#FFB088" />
            <circle cx="46" cy="36" r="2" fill="#FFB088" />
          </svg>
        </div>
        <p class="empty-title">还没有做过的菜～</p>
        <p class="empty-desc">上传一张买菜截图，让开饭帮你想</p>
        <router-link to="/" class="empty-btn">
          去首页上传
        </router-link>
      </div>

      <!-- 时间轴列表 -->
      <ol v-else class="timeline">
        <li
          v-for="(scheme, idx) in items"
          :key="scheme.id"
          class="timeline-item"
          :style="{ animationDelay: `${idx * 80}ms` }"
        >
          <!-- 时间轴左侧 -->
          <div class="timeline-axis" aria-hidden="true">
            <span class="dot" :class="dotClass(scheme.createdAt)" />
            <span v-if="idx < items.length - 1" class="line" />
          </div>

          <!-- 内容区 -->
          <div class="timeline-content">
            <header class="time-header">
              <span class="time">{{ formatDate(scheme.createdAt) }}</span>
              <button
                type="button"
                class="delete-btn"
                aria-label="删除这条历史"
                @click="openDelete(scheme.id, $event)"
              >
                <Icon name="trash" :size="16" />
              </button>
            </header>

            <div class="dishes">
              <DishCard
                v-for="dish in scheme.dishes"
                :key="dish.id"
                :dish="dish"
                :scheme-id="scheme.id"
                @click="onDishClick"
              />
            </div>
          </div>
        </li>
      </ol>
    </main>

    <BottomTab />

    <!-- 删除确认 sheet -->
    <Transition name="sheet">
      <div v-if="showDelete" class="sheet-mask" @click="closeDelete">
        <div class="sheet" role="dialog" aria-modal="true" @click.stop>
          <div class="sheet-handle" aria-hidden="true" />
          <h2 class="sheet-title">删除这条历史？</h2>
          <p class="sheet-desc">删除后无法恢复</p>
          <button class="sheet-btn-danger" type="button" @click="confirmDelete">
            删除
          </button>
          <button class="sheet-btn-cancel" type="button" @click="closeDelete">
            取消
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.history {
  min-height: 100vh;
  min-height: 100dvh;
  /* 背景图通过 :style 内联绑定；这里只兜底底色 */
  background-color: var(--color-bg-secondary);
  position: relative;
  overflow: hidden;
}

/* 暖色氛围叠加（带模糊，让背景图"远景化"，前景更清晰） */
.bg {
  position: absolute;
  inset: 0;
  background: var(--bg-warm-radial);
  backdrop-filter: blur(14px) saturate(120%);
  -webkit-backdrop-filter: blur(14px) saturate(120%);
  opacity: 0.45;
  pointer-events: none;
  z-index: 0;
}

.content {
  padding: var(--space-4) var(--space-4) calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-8));
  padding-top: calc(var(--safe-top) + var(--size-topbar) + var(--space-2));
  position: relative;
  z-index: 1;
}

/* === 空状态 === */
.empty {
  margin-top: var(--space-16);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.empty-icon {
  margin-bottom: var(--space-4);
  filter: drop-shadow(0 4px 16px rgba(255, 122, 69, 0.15));
}

.empty-title {
  font-size: var(--text-h3);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.empty-desc {
  font-size: var(--text-body-sm);
  color: var(--color-text-tertiary);
  margin: 0;
}

.empty-btn {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-8);
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  font-size: var(--text-body-sm);
  font-weight: var(--font-medium);
  text-decoration: none;
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.empty-btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}

/* === 时间轴 === */
.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline-item {
  display: flex;
  gap: var(--space-3);
  opacity: 0;
  transform: translateY(12px);
  animation: item-enter var(--duration-emphasis) var(--ease-emphasis) forwards;
  margin-bottom: var(--space-5);
}

@keyframes item-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 左侧时间轴：圆点 + 连接线 */
.timeline-axis {
  flex: 0 0 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  background: var(--color-bg-tertiary);
  border: 2px solid var(--color-bg-secondary);
  box-shadow: 0 0 0 2px transparent;
  flex: 0 0 auto;
}

.dot-hot {
  background: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(255, 122, 69, 0.15);
}

.dot-warm {
  background: var(--color-primary-light);
}

.dot-cool {
  background: var(--color-text-tertiary);
}

.line {
  flex: 1;
  width: 2px;
  background: var(--color-divider);
  margin-top: var(--space-1);
  min-height: 40px;
}

/* 内容区 */
.timeline-content {
  flex: 1;
  min-width: 0;
}

.time-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.time {
  font-size: var(--text-caption);
  color: var(--color-text-tertiary);
  font-weight: var(--font-medium);
  letter-spacing: 0.5px;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  background: transparent;
  transition:
    background-color var(--duration-fast) var(--ease-default),
    color var(--duration-fast) var(--ease-default);
}

.delete-btn:active {
  background-color: rgba(231, 76, 60, 0.1);
  color: var(--color-error);
}

.dishes {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* === sheet（与 Mine 共用样式） === */
.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(42, 37, 32, 0.45);
  z-index: var(--z-modal);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.sheet {
  width: 100%;
  max-width: 480px;
  background: var(--color-bg);
  border-radius: var(--radius-3xl) var(--radius-3xl) 0 0;
  padding: var(--space-4) var(--space-6) calc(var(--safe-bottom) + var(--space-6));
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  text-align: center;
}

.sheet-handle {
  width: 40px;
  height: 4px;
  border-radius: var(--radius-full);
  background: var(--color-border);
  margin: 0 auto var(--space-2);
}

.sheet-title {
  font-size: var(--text-h3);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: var(--space-2) 0 0;
}

.sheet-desc {
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  margin: 0 var(--space-4) var(--space-2);
}

.sheet-btn-danger {
  height: 52px;
  background: var(--color-error);
  color: var(--color-text-inverse);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
}

.sheet-btn-danger:active {
  opacity: 0.85;
}

.sheet-btn-cancel {
  height: 52px;
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
}

.sheet-btn-cancel:active {
  opacity: 0.85;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity var(--duration-normal) var(--ease-default);
}
.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform var(--duration-medium) var(--ease-spring);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(100%);
}
</style>