<script setup lang="ts">
/**
 * 菜品卡片（左图右文）
 * 来源：docs/Design.md §3.2.1 + PRD §3.2.3.1
 * 用法：Result.vue / Done.vue 共用
 */
import type { Dish } from '@/stores/dish'

interface Props {
  dish: Dish
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'click', dish: Dish): void
}>()
</script>

<template>
  <button
    class="dish-card"
    type="button"
    @click="emit('click', dish)"
  >
    <!-- 左侧图片：MVP 无配图时显示占位 -->
    <div class="dish-image">
      <img
        v-if="dish.previewImage"
        :src="dish.previewImage"
        :alt="dish.name"
        loading="lazy"
      />
      <span v-else class="placeholder" aria-hidden="true">🍽</span>
    </div>

    <!-- 右侧文本 -->
    <div class="dish-body">
      <div class="dish-name">{{ dish.name }}</div>
      <div class="dish-desc">{{ dish.description }}</div>
      <div class="dish-meta">
        <span class="clock" aria-hidden="true">⏱</span>
        <span>{{ dish.estimatedTime }}</span>
      </div>
    </div>

    <!-- 右侧箭头 -->
    <div class="dish-arrow" aria-hidden="true">›</div>
  </button>
</template>

<style scoped>
.dish-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  width: 100%;
  padding: var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  text-align: left;
  transition:
    transform var(--duration-fast) var(--ease-default),
    box-shadow var(--duration-fast) var(--ease-default);
}

.dish-card:active {
  transform: scale(0.98);
  box-shadow: var(--shadow-card-hover);
}

/* === 左侧图片 === */
.dish-image {
  flex: 0 0 96px;
  width: 96px;
  height: 96px;
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dish-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  font-size: 40px;
  line-height: 1;
  opacity: 0.5;
}

/* === 右侧文本 === */
.dish-body {
  flex: 1;
  min-width: 0; /* 允许文本在 flex 中省略 */
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.dish-name {
  font-size: var(--text-h2); /* 24px */
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dish-desc {
  font-size: var(--text-body-sm); /* 16px */
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dish-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-caption); /* 14px */
  color: var(--color-text-tertiary);
  line-height: 1.4;
}

.clock {
  font-size: 14px;
}

/* === 右侧箭头 === */
.dish-arrow {
  flex: 0 0 auto;
  font-size: 20px;
  line-height: 1;
  color: var(--color-text-tertiary);
  /* 视觉居中微调 */
  transform: translateY(-1px);
}
</style>