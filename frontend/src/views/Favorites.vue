<script setup lang="ts">
/**
 * 我的收藏（已登录态）
 * 视觉：标题区 + 治愈空状态
 */
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import BottomTab from '@/components/BottomTab.vue'
import DishCard from '@/components/DishCard.vue'
import Icon from '@/components/Icon.vue'
import TopBar from '@/components/TopBar.vue'
import type { Dish } from '@/stores/dish'
import { useDishStore } from '@/stores/dish'
import { useAuthStore } from '@/stores/auth'
import { useFavoritesStore } from '@/stores/favorites'

// 收藏背景图
import favoritesBg from '@/assets/favorites-bg.png'

const router = useRouter()
const dishStore = useDishStore()
const auth = useAuthStore()
const favorites = useFavoritesStore()

const items = computed(() => favorites.list)
const isEmpty = computed(() => items.value.length === 0)
const count = computed(() => items.value.length)

onMounted(async () => {
  if (!auth.isAuthenticated) {
    router.replace({ name: 'login', query: { redirect: '/mine/favorites' } })
    return
  }
  try {
    await Promise.all([
      favorites.fetchList(),
      dishStore.loadRemoteHistory(),
    ])
  } catch (e) {
    console.warn('拉取收藏失败', e)
  }
})

function onDishClick(dish: Dish) {
  const matchedScheme = dishStore.history.find((s) =>
    s.dishes.some((d) => d.id === dish.id),
  )
  if (matchedScheme) {
    dishStore.loadFromHistory(matchedScheme.id)
    router.push({ name: 'result' })
  } else {
    dishStore.currentScheme = {
      id: `fav-${dish.id}`,
      dishes: [dish],
      carbRecommendation: { name: '', reason: '' },
      createdAt: Date.now(),
    }
    router.push({ name: 'result' })
  }
}
</script>

<template>
  <div
    class="favorites page"
    :style="{
      backgroundImage: `url(${favoritesBg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center 18%',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'scroll',
    }"
  >
    <!-- 背景图上的极淡暖色氛围 -->
    <div class="bg" aria-hidden="true" />

    <TopBar title="我的收藏" back-to="mine" />

    <main class="content">
      <!-- 加载态 -->
      <p v-if="favorites.loading && isEmpty" class="loading">加载中…</p>

      <!-- 空状态 -->
      <div v-else-if="isEmpty" class="empty">
        <div class="empty-icon" aria-hidden="true">
          <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
            <!-- 暖色圆形背景 -->
            <circle cx="60" cy="60" r="56" fill="#FFE8D9" />
            <!-- 碗 -->
            <path
              d="M28 56h64 a24 24 0 0 1-48 0 a24 24 0 0 1 48 0"
              stroke="#C2623A"
              stroke-width="2.5"
              stroke-linecap="round"
              fill="#FFFFFF"
            />
            <!-- 碗内装饰线 -->
            <path
              d="M40 60h40"
              stroke="#C2623A"
              stroke-width="1.5"
              stroke-linecap="round"
              opacity="0.3"
            />
            <!-- 上方空心爱心（暗示"待收藏"）-->
            <path
              d="M60 32c-3-4-9-4-9 1 c0 4 9 11 9 11 c0 0 9-7 9-11 c0-5-6-5-9-1Z"
              stroke="#FF7A45"
              stroke-width="2"
              stroke-linejoin="round"
              fill="#FFFFFF"
            />
            <!-- 装饰小点 -->
            <circle cx="32" cy="32" r="3" fill="#FFB088" opacity="0.5" />
            <circle cx="88" cy="84" r="4" fill="#7BC47F" opacity="0.5" />
          </svg>
        </div>
        <h2 class="empty-title">还没有想吃的菜</h2>
        <p class="empty-desc">
          上传买菜截图后
          <br />
          在方案页点
          <span class="inline-star" aria-hidden="true">
            <Icon name="star" :size="14" />
          </span>
          收藏喜欢的菜
        </p>
        <router-link to="/" class="empty-btn">
          去首页逛逛
        </router-link>
      </div>

      <!-- 列表：标题 + 卡片都包在玻璃容器里，与背景图分离 -->
      <template v-else>
        <section class="glass hero-card">
          <h2 class="hero-title">心选之味</h2>
          <p class="hero-subtitle">共 {{ count }} 道菜 · 想做的时候随时找回来</p>
        </section>

        <ul class="list">
          <li
            v-for="(fav, idx) in items"
            :key="fav.id"
            class="list-item"
            :style="{ animationDelay: `${idx * 60}ms` }"
          >
            <DishCard
              :dish="fav.dish_payload"
              :scheme-id="fav.scheme_id"
              @click="onDishClick"
            />
          </li>
        </ul>
      </template>
    </main>

    <BottomTab />
  </div>
</template>

<style scoped>
.favorites {
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
  padding: var(--space-4);
  padding-top: calc(var(--safe-top) + var(--size-topbar) + var(--space-2));
  padding-bottom: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-8));
  position: relative;
  z-index: 1;
}

.loading {
  margin-top: var(--space-16);
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-body-sm);
}

/* === 标题区（玻璃卡） === */
.hero-card {
  margin: var(--space-4) var(--space-2) var(--space-6);
  padding: var(--space-5) var(--space-6);
}

.hero-title {
  font-size: var(--text-h1);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  letter-spacing: 2px;
  margin: 0;
}

.hero-subtitle {
  margin: var(--space-2) 0 0;
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
}

/* === Frosted Glass（与 Mine 同款） === */
.glass {
  background: rgba(255, 255, 255, 0.78);
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  box-shadow:
    0 1px 2px rgba(42, 37, 32, 0.04),
    0 8px 32px rgba(42, 37, 32, 0.08);
}

/* === 空状态 === */
.empty {
  margin-top: var(--space-12);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.empty-icon {
  margin-bottom: var(--space-4);
  filter: drop-shadow(0 8px 24px rgba(194, 98, 58, 0.15));
  animation: float 4s var(--ease-default) infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
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
  line-height: 1.7;
  text-align: center;
  margin: 0;
}

.inline-star {
  display: inline-flex;
  vertical-align: -2px;
  margin: 0 var(--space-1);
  color: var(--color-text-primary);
}

.inline-star :deep(svg) {
  stroke-width: 1.8;
}

.empty-btn {
  margin-top: var(--space-6);
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

/* === 列表 === */
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.list-item {
  opacity: 0;
  transform: translateY(12px);
  animation: item-enter var(--duration-emphasis) var(--ease-emphasis) forwards;
}

@keyframes item-enter {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>