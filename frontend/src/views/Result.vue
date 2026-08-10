<script setup lang="ts">
/**
 * 菜谱结果页
 * 来源：用户最新需求（2026-07-29）—— 居中布局 + 中间按钮
 *
 * 布局：
 *   [透明顶部：仅退出按钮]
 *   [标题：开饭为你推荐这 N 道菜 ^ ^]
 *   [菜品卡片，居中]
 *   [换一批菜 按钮，居中，胶囊灰色边框]
 */
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DishCard from '@/components/DishCard.vue'
import { useDishStore, type Dish } from '@/stores/dish'

const router = useRouter()
const dishStore = useDishStore()

/* === 方案数据 === */
const dishes = computed<Dish[]>(() => dishStore.currentScheme?.dishes ?? [])
const hasScheme = computed(() => dishes.value.length > 0)

/* === 卡片浮现动画 === */
/* 用 v-for + 内联 style 设 animationDelay，每张间隔 150ms */

onMounted(() => {
  /* 没有方案时回到首页（异常路径） */
  if (!hasScheme.value) {
    router.replace({ name: 'home' })
  }
})

function onDishClick(dish: Dish) {
  router.push({ name: 'dish-detail', params: { dishId: dish.id } })
}

function onRefresh() {
  /* 换一批：限制 3 次。history 保留最近 2 轮菜名，避免 prompt 太长 */
  if (dishStore.refreshCount >= dishStore.MAX_REFRESH_COUNT) {
    return
  }

  // 收集当前菜名作为 exclusion list
  const currentNames = dishStore.currentScheme?.dishes.map((d) => d.name) ?? []

  // 合并到 history（保留最近 2 轮，最多 ~6 个菜名）
  const newHistory = [...dishStore.historyDishNames, ...currentNames].slice(-6)
  // 去重
  const dedupHistory = Array.from(new Set(newHistory))

  dishStore.setHistoryDishNames(dedupHistory)
  dishStore.incrementRefreshCount()
  dishStore.currentScheme = null
  router.push({ name: 'loading' })
}

function onExit() {
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="result page">
    <!-- 透明顶部：仅退出按钮 -->
    <header class="result-header">
      <button
        class="exit-btn"
        type="button"
        aria-label="退出"
        @click="onExit"
      >
        <span aria-hidden="true">‹</span>
      </button>
    </header>

    <main class="result-main">
      <!-- 标题 -->
      <h1 class="result-title">
        开饭为你推荐这 {{ dishes.length }} 道菜
        <span class="smiley">^ ^</span>
      </h1>

      <!-- 菜品卡片 -->
      <div class="dish-list">
        <DishCard
          v-for="(dish, idx) in dishes"
          :key="dish.id"
          :dish="dish"
          :scheme-id="dishStore.currentScheme?.id"
          :style="{ animationDelay: `${idx * 150}ms` }"
          class="dish-card-anim"
          @click="onDishClick"
        />
      </div>

      <!-- 换一批菜：3 次上限 -->
      <button
        class="refresh-btn"
        type="button"
        :disabled="dishStore.refreshCount >= dishStore.MAX_REFRESH_COUNT"
        @click="onRefresh"
      >
        <span v-if="dishStore.refreshCount >= dishStore.MAX_REFRESH_COUNT">
          已达换一批上限
        </span>
        <span v-else>
          换一批菜
          <span v-if="dishStore.refreshCount > 0" class="refresh-hint">
            （{{ dishStore.MAX_REFRESH_COUNT - dishStore.refreshCount }} 次剩余）
          </span>
        </span>
      </button>
    </main>
  </div>
</template>

<style scoped>
.result {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-bg);
}

/* === 透明顶部 === */
.result-header {
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

/* === 主内容：居中 === */
.result-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-6) var(--space-4);
  padding-top: calc(var(--safe-top) + var(--size-topbar) + var(--space-6));
  gap: var(--space-8);
}

/* === 标题 === */
.result-title {
  font-size: var(--text-h3); /* 20px */
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
  text-align: center;
  margin: 0;
}

.smiley {
  margin-left: var(--space-1);
  color: var(--color-text-secondary);
  font-weight: var(--font-regular);
}

/* === 菜品卡片列表 === */
.dish-list {
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
}

/* 卡片浮现动画 */
.dish-card-anim {
  width: 100%;
  opacity: 0;
  transform: translateY(16px);
  animation: card-enter var(--duration-emphasis) var(--ease-emphasis) forwards;
}

@keyframes card-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* === 换一批菜：居中胶囊按钮 === */
.refresh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: var(--size-button); /* 48px */
  padding: 0 var(--space-8);
  background: var(--color-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--text-body-sm); /* 16px */
  font-weight: var(--font-medium);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.refresh-btn:active:not(:disabled) {
  opacity: 0.85;
  transform: scale(0.98);
}

.refresh-btn:disabled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
  cursor: not-allowed;
  opacity: 0.7;
}

.refresh-hint {
  font-size: 12px;
  margin-left: var(--space-2);
  color: var(--color-text-tertiary);
  font-weight: var(--font-regular);
}
</style>