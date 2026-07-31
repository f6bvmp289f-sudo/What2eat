<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

interface TabItem {
  key: string
  label: string
  /** 路由名，点击跳转 */
  to?: string
  /** 是否 MVP 暂未实现 */
  disabled?: boolean
}

const tabs: TabItem[] = [
  { key: 'home', label: '首页', to: '/' },
  { key: 'favorite', label: '收藏', disabled: true },
  { key: 'kitchen', label: '厨房', disabled: true },
]

function onTabClick(tab: TabItem) {
  if (tab.disabled) {
    // MVP 阶段：提示敬请期待
    // 实际项目中可换成全局 toast
    alert('敬请期待～')
    return
  }
  if (tab.to && route.path !== tab.to) {
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
      :class="{ active: tab.to === route.path }"
      :disabled="tab.disabled"
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

.tab-item:disabled {
  cursor: not-allowed;
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
