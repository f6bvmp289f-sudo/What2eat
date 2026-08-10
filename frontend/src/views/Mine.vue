<script setup lang="ts">
/**
 * 我的主页（v2 · Frosted Glass 沉浸版）
 *
 * 信息架构（自上而下 5 块玻璃面板）：
 *   1. 用户卡（hash 选色头像 + 用户名 + 加入日期 + 设置）
 *   2. 统计行（3 列：已做 / 收藏 / 共度天数）
 *   3. 最近做过（最近一道菜的 mini card，有数据才显示）
 *   4. 我的（菜单卡，title 合并到卡头；历史记录 / 收藏）
 *   5. 退出登录（独立玻璃卡，告别裸飘按钮）
 *
 * 视觉：所有面板统一 frosted glass（rgba 0.78 + blur 20px saturate 180% + 浅边框 + 悬浮阴影）
 * 背景：工笔画食材插画（PNG）通过 :style 内联绑到容器
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BottomTab from '@/components/BottomTab.vue'
import DishCard from '@/components/DishCard.vue'
import Icon from '@/components/Icon.vue'
import type { Dish, DishScheme } from '@/stores/dish'
import { useAuthStore } from '@/stores/auth'
import { useDishStore } from '@/stores/dish'
import { useFavoritesStore } from '@/stores/favorites'

// 我的页背景图（工笔画风格食材插画）
import mineBg from '@/assets/mine-bg.png'

const router = useRouter()
const auth = useAuthStore()
const dishStore = useDishStore()
const favorites = useFavoritesStore()

const joinedAt = computed(() => {
  const ts = auth.user?.created_at
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`
})

const daysJoined = computed(() => {
  const ts = auth.user?.created_at
  if (!ts) return 0
  const diff = Date.now() - ts
  return Math.max(1, Math.floor(diff / 86400_000))
})

// ===== 数据 =====
const totalDishes = computed(() =>
  dishStore.history.reduce((sum, s) => sum + s.dishes.length, 0),
)

const favoritesCount = computed(() => favorites.list.length)

onMounted(async () => {
  if (auth.isAuthenticated) {
    try {
      await Promise.all([
        dishStore.loadRemoteHistory(),
        favorites.fetchList(),
      ])
    } catch (e) {
      console.warn('我的页数据同步失败', e)
    }
  }
})

const latest = computed<{ scheme: DishScheme; dish: Dish } | null>(() => {
  const list = dishStore.history
  if (list.length === 0) return null
  const scheme = list[0]
  const dish = scheme.dishes[0]
  if (!dish) return null
  return { scheme, dish }
})

function goHistory() {
  router.push({ name: 'mine-history' })
}

function goFavorites() {
  router.push({ name: 'mine-favorites' })
}

function onLatestClick(dish: Dish) {
  const matched = dishStore.history.find((s) =>
    s.dishes.some((d) => d.id === dish.id),
  )
  if (matched) {
    dishStore.loadFromHistory(matched.id)
    router.push({ name: 'result' })
  }
}

// ===== 退出登录 sheet =====
const showLogout = ref(false)

function openLogout() {
  showLogout.value = true
}

function closeLogout() {
  showLogout.value = false
}

async function confirmLogout() {
  const { useHistoryStore } = await import('@/stores/history')
  useHistoryStore().clearRemote()
  favorites.clearFavorites()
  dishStore.clearHistory()
  auth.logout()
  closeLogout()
  router.replace({ name: 'home' })
}
</script>

<template>
  <div
    class="mine page"
    :style="{
      backgroundImage: `url(${mineBg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center top',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'scroll',
    }"
  >
    <!-- 背景图之上、玻璃面板之下的极淡暖色氛围（让背景图"暖"起来一点点） -->
    <div class="bg-overlay" aria-hidden="true" />

    <main class="content">
      <!-- 1. 用户卡（玻璃） -->
      <header class="glass profile-card">
        <div class="profile-info">
          <h1 class="username">{{ auth.user?.username }}</h1>
          <p class="meta">
            <span class="meta-dot" aria-hidden="true" />
            <span>加入于 {{ joinedAt }}</span>
          </p>
        </div>
        <button
          class="settings-btn"
          type="button"
          aria-label="设置"
        >
          <Icon name="logout" :size="20" />
        </button>
      </header>

      <!-- 2. 统计行（玻璃） -->
      <section class="glass stats" aria-label="使用统计">
        <div class="stat">
          <div class="stat-num">{{ totalDishes }}</div>
          <div class="stat-label">已做菜谱</div>
        </div>
        <div class="stat-divider" aria-hidden="true" />
        <div class="stat">
          <div class="stat-num">{{ favoritesCount }}</div>
          <div class="stat-label">已收藏</div>
        </div>
        <div class="stat-divider" aria-hidden="true" />
        <div class="stat">
          <div class="stat-num">{{ daysJoined }}</div>
          <div class="stat-label">共度天数</div>
        </div>
      </section>

      <!-- 3. 最近做过（玻璃，有数据才显示） -->
      <section v-if="latest" class="glass latest-card">
        <header class="card-header">
          <h2 class="card-title">最近做过</h2>
          <button class="card-more" type="button" @click="goHistory">
            查看全部
          </button>
        </header>
        <DishCard
          :dish="latest.dish"
          :scheme-id="latest.scheme.id"
          @click="onLatestClick"
        />
      </section>

      <!-- 4. 我的（玻璃；title 合并到卡头） -->
      <section class="glass menu-card">
        <header class="card-header">
          <h2 class="card-title">我的</h2>
        </header>
        <ul class="menu-list">
          <li>
            <button class="menu-item" type="button" @click="goHistory">
              <span class="menu-icon menu-icon-history" aria-hidden="true">
                <Icon name="clock" :size="22" />
              </span>
              <span class="menu-label">历史记录</span>
              <span
                v-if="dishStore.history.length > 0"
                class="menu-badge"
              >
                {{ dishStore.history.length }}
              </span>
              <span class="menu-arrow" aria-hidden="true">
                <Icon name="chevron-right" :size="18" />
              </span>
            </button>
          </li>
          <li>
            <button class="menu-item" type="button" @click="goFavorites">
              <span class="menu-icon menu-icon-favorites" aria-hidden="true">
                <Icon name="star" :size="22" />
              </span>
              <span class="menu-label">收藏</span>
              <span
                v-if="favoritesCount > 0"
                class="menu-badge menu-badge-warm"
              >
                {{ favoritesCount }}
              </span>
              <span class="menu-arrow" aria-hidden="true">
                <Icon name="chevron-right" :size="18" />
              </span>
            </button>
          </li>
        </ul>
      </section>

      <!-- 5. 退出登录（独立玻璃卡，居中、胶囊弱化） -->
      <button class="glass logout-card" type="button" @click="openLogout">
        退出登录
      </button>
    </main>

    <BottomTab />

    <!-- 退出登录 sheet -->
    <Transition name="sheet">
      <div v-if="showLogout" class="sheet-mask" @click="closeLogout">
        <div class="sheet" role="dialog" aria-modal="true" @click.stop>
          <div class="sheet-handle" aria-hidden="true" />
          <h2 class="sheet-title">退出登录？</h2>
          <p class="sheet-desc">
            退出后将无法查看历史记录和收藏，下次需要重新登录。
          </p>
          <button class="sheet-btn-danger" type="button" @click="confirmLogout">
            退出登录
          </button>
          <button class="sheet-btn-cancel" type="button" @click="closeLogout">
            取消
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.mine {
  min-height: 100vh;
  min-height: 100dvh;
  /* 背景图通过 :style 内联绑定；这里只兜底底色 */
  background-color: var(--color-bg-secondary);
  padding-bottom: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-6));
  position: relative;
  overflow: hidden;
}

/* === 极淡暖色氛围叠加（让背景图"暖"一点点） === */
.bg-overlay {
  position: absolute;
  inset: 0;
  background: var(--bg-warm-radial);
  opacity: 0.15;
  pointer-events: none;
  z-index: 0;
}

/* === 内容容器：顶部 88px 留白，让背景图顶部装饰露出 === */
.content {
  position: relative;
  z-index: 1;
  padding: calc(var(--safe-top) + var(--space-10)) var(--space-4) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* ======================================================
 * Frosted Glass 公共样式（4 张面板共用）
 * Glassmorphism 规范：blur 10-20px + 浅边框 + Z-depth 分层
 * ====================================================== */
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

/* === 1. 用户卡 === */
.profile-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.username {
  font-size: var(--text-h2);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  line-height: 1.3;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-body-sm);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0;
}

.meta-dot {
  width: 4px;
  height: 4px;
  border-radius: var(--radius-full);
  background: var(--color-text-tertiary);
}

.settings-btn {
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  background: rgba(255, 255, 255, 0.4);
  transition:
    background-color var(--duration-fast) var(--ease-default),
    color var(--duration-fast) var(--ease-default);
}

.settings-btn:active {
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-text-primary);
}

/* === 2. 统计行 === */
.stats {
  display: flex;
  align-items: stretch;
  padding: var(--space-5) var(--space-4);
}

.stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  text-align: center;
}

.stat-num {
  font-size: 28px;
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: var(--text-caption);
  color: var(--color-text-tertiary);
}

.stat-divider {
  width: 1px;
  align-self: stretch;
  margin: var(--space-1) 0;
  background: rgba(42, 37, 32, 0.1);
}

/* === 卡片通用 header（最近做过 / 我的 共用） === */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5) var(--space-2);
}

.card-title {
  font-size: var(--text-body);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.card-more {
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  background: transparent;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  transition: color var(--duration-fast) var(--ease-default);
}

.card-more:active {
  color: var(--color-text-primary);
}

/* === 3. 最近做过 === */
.latest-card {
  /* DishCard 自身已经是一张卡，所以卡内 padding 收紧让它"贴边"显示 */
  padding: 0;
}

.latest-card .card-header {
  padding-top: var(--space-4);
}

.latest-card :deep(.dish-card) {
  /* DishCard 在玻璃卡里再去掉自己的 box-shadow，避免双层阴影 */
  margin: 0 var(--space-4) var(--space-4);
  box-shadow: none;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* === 4. 我的（菜单） === */
.menu-card {
  padding: 0;
}

.menu-card .card-header {
  padding-bottom: 0;
}

.menu-list {
  list-style: none;
  margin: 0;
  padding: 0 var(--space-1) var(--space-2);
}

.menu-list li + li {
  border-top: 1px solid rgba(42, 37, 32, 0.06);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 60px;
  padding: 0 var(--space-4);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.menu-item:active {
  background-color: rgba(42, 37, 32, 0.04);
  transform: scale(0.997);
}

.menu-icon {
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-icon-history {
  background: var(--avatar-1-bg);
  color: var(--avatar-1-fg);
}

.menu-icon-favorites {
  background: var(--avatar-3-bg);
  color: var(--avatar-3-fg);
}

.menu-label {
  flex: 1;
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}

.menu-badge {
  flex: 0 0 auto;
  min-width: 28px;
  height: 24px;
  padding: 0 var(--space-2);
  background: rgba(42, 37, 32, 0.06);
  color: var(--color-text-secondary);
  font-size: var(--text-caption);
  font-weight: var(--font-semibold);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-variant-numeric: tabular-nums;
}

.menu-badge-warm {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.menu-arrow {
  flex: 0 0 auto;
  color: var(--color-text-tertiary);
  display: flex;
  align-items: center;
}

/* === 5. 退出登录（独立玻璃卡） === */
.logout-card {
  margin: var(--space-2) 0 0;
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.55);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-default),
    color var(--duration-fast) var(--ease-default);
}

.logout-card:active {
  background: rgba(231, 76, 60, 0.08);
  color: var(--color-error);
}

/* === sheet（与 History 共用样式） === */
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
  line-height: 1.6;
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