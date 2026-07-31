<script setup lang="ts">
/**
 * 结果页（完成一道菜）
 * 来源：docs/Design.md §4.7 + docs/PRD.md §3.4
 *
 * 视觉：居中大对勾（浅绿底+绿对勾） + "菜名 完成了"
 *       + 庆祝动画（放大缩放 + 星星粒子）
 *       + 剩余菜品卡片列表（点击进下一道菜的教程）
 *
 * MVP：庆祝动画 = 简单放大缩放 + 几颗粒子从中心向四周飞出
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
import DishCard from '@/components/DishCard.vue'
import { useDishStore, type Dish } from '@/stores/dish'

const route = useRoute()
const router = useRouter()
const dishStore = useDishStore()

const dishId = computed(() => String(route.params.dishId || ''))
const dish = computed<Dish | undefined>(() =>
  dishStore.currentScheme?.dishes.find((d) => d.id === dishId.value),
)

/* === 剩余菜品（除当前完成的） === */
const remaining = computed<Dish[]>(() => {
  if (!dishStore.currentScheme) return []
  return dishStore.currentScheme.dishes.filter((d) => d.id !== dishId.value)
})

const allDone = computed(() => remaining.value.length === 0)

/* === 顶栏 title：今天做了 X 道菜 === */
const title = computed(() => {
  const total = dishStore.currentScheme?.dishes.length ?? 0
  return `今天做了 ${total} 道菜`
})

/* === 庆祝动画：8 颗粒子，2 秒 === */
interface Particle {
  id: number
  x: number
  y: number
  angle: number
  color: string
  size: number
}
const particles = ref<Particle[]>([])

function startCelebration() {
  const colors = ['#FFB088', '#FF7A45', '#7BC47F', '#F5A623']
  const newOnes: Particle[] = []
  for (let i = 0; i < 8; i++) {
    const angle = (Math.PI * 2 * i) / 8
    newOnes.push({
      id: i,
      x: Math.cos(angle) * 80,
      y: Math.sin(angle) * 80,
      angle,
      color: colors[i % colors.length],
      size: 8 + Math.random() * 8,
    })
  }
  particles.value = newOnes
}

onMounted(() => {
  if (!dish.value) {
    router.replace({ name: 'home' })
    return
  }
  startCelebration()
})

onBeforeUnmount(() => {
  particles.value = []
})

function onRemainingClick(d: Dish) {
  router.push({ name: 'tutorial', params: { dishId: d.id } })
}

function onGoHome() {
  router.push({ name: 'home' })
}
</script>

<template>
  <div v-if="dish" class="done page">
    <TopBar :title="title" />

    <main class="done-main">
      <!-- 庆祝区：对勾 + 菜名 -->
      <section class="celebrate">
        <div class="check-wrap">
          <div class="check-bg" aria-hidden="true">
            <span class="check">✓</span>
          </div>
          <!-- 粒子 -->
          <span
            v-for="p in particles"
            :key="p.id"
            class="particle"
            :style="{
              '--x': p.x + 'px',
              '--y': p.y + 'px',
              '--c': p.color,
              '--s': p.size + 'px',
            }"
            aria-hidden="true"
          />
        </div>
        <h2 class="dish-name">
          <span class="name">{{ dish.name }}</span>
          <span class="suffix"> 完成了</span>
        </h2>
      </section>

      <!-- 剩余菜品 / 全部完成 -->
      <section class="remaining">
        <h3 v-if="!allDone" class="section-label">继续做下一道</h3>
        <h3 v-else class="section-label">今天的开饭搞定啦 🎉</h3>

        <div v-if="!allDone" class="dish-list">
          <DishCard
            v-for="d in remaining"
            :key="d.id"
            :dish="d"
            @click="onRemainingClick"
          />
        </div>

        <div v-else class="go-home">
          <button class="home-btn" type="button" @click="onGoHome">
            回到首页
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.done {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-bg);
}

.done-main {
  flex: 1;
  padding: var(--space-8) var(--space-4);
  padding-bottom: calc(var(--safe-bottom) + var(--space-8));
}

/* === 庆祝区 === */
.celebrate {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-12) 0 var(--space-10);
}

.check-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pop var(--duration-emphasis) var(--ease-emphasis);
}

.check-bg {
  width: 100px;
  height: 100px;
  border-radius: var(--radius-full);
  background: var(--color-success-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.check {
  font-size: 56px;
  font-weight: var(--font-bold);
  color: var(--color-success);
  line-height: 1;
  transform: translateY(-2px);
}

@keyframes pop {
  0% { transform: scale(0.6); opacity: 0; }
  60% { transform: scale(1.08); opacity: 1; }
  100% { transform: scale(1); }
}

/* === 粒子 === */
.particle {
  position: absolute;
  width: var(--s);
  height: var(--s);
  border-radius: var(--radius-full);
  background: var(--c);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  animation: burst 1500ms var(--ease-emphasis) forwards;
}

@keyframes burst {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 1;
  }
  100% {
    transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(1);
    opacity: 0;
  }
}

/* === 菜名 === */
.dish-name {
  font-size: var(--text-h2); /* 24px */
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: calc(100vw - var(--space-8));
  text-align: center;
}

.name {
  /* 菜名 */
}

.suffix {
  color: var(--color-text-secondary);
  font-weight: var(--font-regular);
}

/* === 剩余菜品 === */
.remaining {
  margin-top: var(--space-8);
}

.section-label {
  font-size: var(--text-h3); /* 20px */
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.dish-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.go-home {
  display: flex;
  justify-content: center;
  margin-top: var(--space-6);
}

.home-btn {
  height: var(--size-button-lg);
  padding: 0 var(--space-8);
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.home-btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}
</style>