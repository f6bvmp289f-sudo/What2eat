<script setup lang="ts">
/**
 * 顶部固定栏
 * 来源：docs/Design.md §3.4 + 各页面 §4.x.2
 * 结构（一致）：[返回箭头] [中间标题] [右侧可选菜单]
 * 高度 44px（不含状态栏），层级 --z-sticky
 */
import { useRouter } from 'vue-router'

interface Props {
  /** 中间标题文字 */
  title: string
  /** 是否显示左侧返回箭头（首页不显示） */
  showBack?: boolean
  /** 返回的目标路由名，默认 home */
  backTo?: string
}

const props = withDefaults(defineProps<Props>(), {
  showBack: true,
  backTo: 'home',
})

const emit = defineEmits<{
  (e: 'back'): void
}>()

const router = useRouter()

function onBack() {
  emit('back')
  router.push({ name: props.backTo })
}
</script>

<template>
  <header class="top-bar">
    <div class="top-bar-left">
      <button
        v-if="showBack"
        class="back-btn"
        type="button"
        aria-label="返回上一页"
        @click="onBack"
      >
        <span class="back-icon" aria-hidden="true">‹</span>
      </button>
    </div>
    <h1 class="top-bar-title">{{ title }}</h1>
    <div class="top-bar-right">
      <!-- 右侧预留插槽（··· 菜单等），未传则空 -->
      <slot name="right" />
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--size-topbar);
  padding: 0 var(--space-3); /* 左右各 12px，给按钮触控空间 */
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  /* 顶部加 safe-top，让 iOS 灵动岛/状态栏不被遮挡 */
  padding-top: var(--safe-top);
  height: calc(var(--size-topbar) + var(--safe-top));
}

.top-bar-left,
.top-bar-right {
  flex: 0 0 var(--size-topbar);
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--size-topbar);
  height: var(--size-topbar);
  border-radius: var(--radius-md);
  transition: opacity var(--duration-fast) var(--ease-default);
}

.back-btn:active {
  opacity: 0.6;
}

.back-icon {
  font-size: 28px;
  line-height: 1;
  color: var(--color-text-primary);
  /* 视觉微调：让 ‹ 居中 */
  transform: translateY(-2px);
}

.top-bar-title {
  flex: 1;
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  line-height: 1;
  color: var(--color-text-primary);
  text-align: center;
  /* 标题过长时省略，避免挤压两侧按钮 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>