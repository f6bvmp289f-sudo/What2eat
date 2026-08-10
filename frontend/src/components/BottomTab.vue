<script setup lang="ts">
/**
 * 底部 Tab
 * 两个 Tab：首页 / 我的
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

interface TabItem {
  key: string
  label: string
  /** 路由路径，点击跳转 */
  to: string
  /** 用于判断 active 的 path 前缀 */
  matchPrefix?: string
}

const tabs: TabItem[] = [
  // 首页的 matchPrefix 留空 —— 它只精确匹配 '/'，避免 catch-all 误命中
  { key: 'home', label: '首页', to: '/' },
  { key: 'mine', label: '我的', to: '/mine', matchPrefix: '/mine' },
]

const activeKey = computed<string>(() => {
  const path = route.path
  // 1) 精确匹配优先
  for (const tab of tabs) {
    if (tab.to === path) return tab.key
  }
  // 2) 前缀匹配（用于 mine 匹配 /mine/*）
  for (const tab of tabs) {
    if (tab.matchPrefix && path.startsWith(tab.matchPrefix)) return tab.key
  }
  return ''
})

function onTabClick(tab: TabItem) {
  if (route.path !== tab.to) {
    router.push(tab.to)
  }
}
</script>

<template>
  <nav class="bottom-tab" role="navigation">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item"
      :class="{ active: activeKey === tab.key }"
      type="button"
      @click="onTabClick(tab)"
    >
      <span class="tab-label">{{ tab.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom-tab {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-fixed);
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: calc(var(--size-tabbar) + var(--safe-bottom));
  padding-bottom: var(--safe-bottom);
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
}

.tab-item {
  flex: 1;
  height: var(--size-tabbar);
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  transition: opacity var(--duration-fast) var(--ease-default);
}

.tab-item:active {
  opacity: 0.6;
}

.tab-label {
  font-size: var(--text-body-sm);
  line-height: 1;
  color: var(--color-text-tertiary);
  transition: color var(--duration-fast) var(--ease-default);
}

.tab-item.active .tab-label {
  color: var(--color-text-primary);
  font-weight: var(--font-semibold);
  font-size: 17px; /* 选中态略大一点 */
}
</style>