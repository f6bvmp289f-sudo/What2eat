<script setup lang="ts">
/**
 * 线性 SVG 图标（24×24，1.5px stroke，圆角端点）
 * 颜色继承 currentColor
 * 用法：<Icon name="clock" :size="20" />
 */
import { computed } from 'vue'

interface Props {
  name:
    | 'clock'
    | 'star'
    | 'star-filled'
    | 'logout'
    | 'chevron-right'
    | 'trash'
    | 'bowl'
    | 'arrow-right'
  size?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  size: 24,
})

const path = computed(() => {
  switch (props.name) {
    case 'clock':
      // 时钟（历史记录入口）
      return 'M12 6v6l4 2 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'
    case 'star':
      // 空心星（收藏入口）
      return 'M12 3.5l2.6 5.6 6.1.7-4.6 4.2 1.3 6L12 17l-5.4 3 1.3-6L3.3 9.8l6.1-.7L12 3.5Z'
    case 'star-filled':
      // 实心星
      return 'M12 3.5l2.6 5.6 6.1.7-4.6 4.2 1.3 6L12 17l-5.4 3 1.3-6L3.3 9.8l6.1-.7L12 3.5Z'
    case 'logout':
      // 退出登录
      return 'M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3 M10 8l-4 4 4 4 M6 12h12'
    case 'chevron-right':
      // 右箭头（菜单项）
      return 'M9 6l6 6-6 6'
    case 'trash':
      // 删除
      return 'M4 7h16 M9 7V4h6v3 M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13 M10 11v6 M14 11v6'
    case 'bowl':
      // 空碗（空状态插画）
      return 'M3 11h18 a9 9 0 0 1-18 0Z M12 4 v3 M8 5.5l1.5 1.5 M16 5.5l-1.5 1.5'
    case 'arrow-right':
      // 右箭头（文字按钮后缀）
      return 'M5 12h14 M13 6l6 6-6 6'
  }
})

const isFilled = computed(
  () => props.name === 'star-filled',
)
</script>

<template>
  <svg
    class="icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke="isFilled ? 'currentColor' : 'none'"
    :stroke-width="isFilled ? 0 : 1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    role="img"
  >
    <path v-if="isFilled" :d="path" />
    <path v-else :d="path" stroke="currentColor" />
  </svg>
</template>

<style scoped>
.icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>