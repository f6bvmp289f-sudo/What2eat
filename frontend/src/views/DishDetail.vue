<script setup lang="ts">
/**
 * 菜品详情页
 * 来源：用户需求（2026-07-29）—— 点击 Result 卡片进入详情，详情页点击"开始做菜"才进入教程
 *
 * 布局：
 *   [透明顶部：仅退出按钮]
 *   [菜品大图（白底高级白盘俯拍）]
 *   [菜名]
 *   [所需材料 pill 标签]
 *   [口味]
 *   [预计耗时]
 *   [底部固定区：☆ 收藏 + 开始做菜]
 */
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDishStore, type Dish } from '@/stores/dish'

const route = useRoute()
const router = useRouter()
const dishStore = useDishStore()

const dishId = computed(() => String(route.params.dishId || ''))
const dish = computed<Dish | undefined>(() =>
  dishStore.currentScheme?.dishes.find((d) => d.id === dishId.value),
)

onMounted(() => {
  if (!dish.value) {
    router.replace({ name: 'result' })
  }
})

function onExit() {
  router.push({ name: 'result' })
}

function onStart() {
  router.push({ name: 'tutorial', params: { dishId: dishId.value } })
}

function onFavorite() {
  /* MVP 收藏功能未实现，先打桩 */
  alert('敬请期待～')
}
</script>

<template>
  <div v-if="dish" class="dish-detail page">
    <!-- 透明顶部：仅退出按钮 -->
    <header class="detail-header">
      <button
        class="exit-btn"
        type="button"
        aria-label="返回"
        @click="onExit"
      >
        <span aria-hidden="true">‹</span>
      </button>
    </header>

    <main class="detail-main">
      <!-- 菜品大图 -->
      <div class="hero">
        <img v-if="dish.previewImage" :src="dish.previewImage" :alt="dish.name" />
        <div v-else class="hero-placeholder" aria-hidden="true">
          <span class="placeholder-emoji">🍽</span>
        </div>
      </div>

      <!-- 文字信息 -->
      <section class="info">
        <h1 class="dish-name">{{ dish.name }}</h1>

        <!-- 所需材料 -->
        <div class="info-block">
          <h3 class="info-label">所需材料</h3>
          <div class="ingredients">
            <span
              v-for="ing in dish.mainIngredients"
              :key="ing"
              class="ingredient-pill"
            >
              {{ ing }}
            </span>
          </div>
        </div>

        <!-- 口味 -->
        <div class="info-block">
          <h3 class="info-label">口味</h3>
          <p class="info-text">{{ dish.taste }}</p>
        </div>

        <!-- 预计耗时 -->
        <div class="info-block">
          <h3 class="info-label">预计耗时</h3>
          <p class="info-text info-text-time">{{ dish.estimatedTime }}</p>
        </div>
      </section>
    </main>

    <!-- 底部固定区：收藏 + 开始做菜 -->
    <footer class="bottom-bar">
      <button
        class="fav-btn"
        type="button"
        aria-label="收藏"
        @click="onFavorite"
      >
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path
            d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"
            fill="currentColor"
          />
        </svg>
      </button>
      <button
        class="start-btn"
        type="button"
        @click="onStart"
      >
        开始做菜
      </button>
    </footer>
  </div>
</template>

<style scoped>
.dish-detail {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-bg);
}

/* === 透明顶部 === */
.detail-header {
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
.detail-main {
  flex: 1;
  padding-top: calc(var(--safe-top) + var(--size-topbar));
  padding-bottom: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-3));
}

/* === 菜品大图 === */
.hero {
  width: calc(100vw - var(--space-4) * 2);
  margin: var(--space-3) var(--space-4) var(--space-6);
  aspect-ratio: 1 / 1;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-bg-secondary);
  box-shadow: var(--shadow-card);
}

.hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
}

.placeholder-emoji {
  font-size: 80px;
  opacity: 0.4;
}

/* === 信息区 === */
.info {
  padding: 0 var(--space-6);
}

.dish-name {
  font-size: var(--text-h2); /* 24px */
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-6);
  line-height: 1.3;
}

.info-block {
  margin-bottom: var(--space-5);
}

.info-label {
  font-size: var(--text-body-sm); /* 16px */
  font-weight: var(--font-regular);
  color: var(--color-text-tertiary);
  margin: 0 0 var(--space-2);
}

.info-text {
  font-size: var(--text-body); /* 18px */
  color: var(--color-text-primary);
  line-height: 1.5;
  margin: 0;
}

.info-text-time {
  color: var(--color-text-primary);
  font-weight: var(--font-medium);
}

/* === 材料 pill 标签 === */
.ingredients {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.ingredient-pill {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  font-size: var(--text-body-sm);
  color: var(--color-text-primary);
}

/* === 底部固定区 === */
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-fixed);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  padding-bottom: calc(var(--safe-bottom) + var(--space-3));
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
}

/* ☆ 收藏：圆形按钮 */
.fav-btn {
  flex: 0 0 auto;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-tertiary);
  transition: opacity var(--duration-fast) var(--ease-default);
}

.fav-btn:active {
  opacity: 0.6;
}

.fav-btn svg {
  width: 22px;
  height: 22px;
}

/* 开始做菜：主按钮 */
.start-btn {
  flex: 1;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-full);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.start-btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}
</style>