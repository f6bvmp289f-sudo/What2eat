<script setup lang="ts">
import { useRouter } from 'vue-router'
import BottomTab from '@/components/BottomTab.vue'
import homeBg from '@/assets/home-bg.png'

const router = useRouter()

/**
 * 点击「现在开始做菜」按钮：直接进入对话页
 * 用户在 /chat 里通过对话输入菜品 / 上传截图
 */
function onUploadClick() {
  router.push({ name: 'chat' })
}
</script>

<template>
  <div class="home page">
    <!-- 工笔画背景图 -->
    <img class="home-bg" :src="homeBg" alt="" aria-hidden="true" />

    <!-- 中间内容区 -->
    <main class="home-content">
      <div class="title-group">
        <h1 class="title">随时准备帮你想好</h1>
        <h1 class="title">今天晚上吃什么</h1>
      </div>

      <div class="action-group">
        <button
          class="upload-btn"
          type="button"
          aria-label="现在开始做菜"
          @click="onUploadClick"
        >
          现在开始做菜
        </button>
        <p class="subtitle">买菜截图、对话输入菜品都可以</p>
      </div>
    </main>

    <!-- 底部 Tab -->
    <BottomTab />
  </div>
</template>

<style scoped>
.home {
  width: 100%;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  position: relative;
}

/* === 背景图：底层，不滚动 === */
.home-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  z-index: var(--z-base);
  pointer-events: none;
  user-select: none;
}

/* === 中间内容：靠下到背景图中央留白区域 === */
.home-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 40vh var(--space-10) 0;
  /* 40vh 让内容从屏幕 40% 开始，整体落在背景图中央偏下的留白处 */
  /* 顶部 40% 是装饰元素密集区（南瓜、花叶），中间 20% 为留白，下方再避开豆角/月饼/生肉 */
}

.title-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-12);
}

.title {
  font-size: var(--text-h1);
  font-weight: var(--font-medium);
  line-height: 1.5;
  color: var(--color-text-primary);
  text-align: center;
  letter-spacing: 0.5px;
}

/* === 操作区：按钮 + 副标题 === */
.action-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.upload-btn {
  /* 左右各 40px（--space-10），符合 Design §4.1.2 */
  width: calc(100vw - var(--space-10) * 2);
  max-width: 22rem; /* 兜底：超大屏也不要太宽 */
  height: 3.25rem; /* 52px */
  padding: 0 var(--space-8);
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  line-height: 1;
  letter-spacing: 1px;
  border-radius: var(--radius-full);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.upload-btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}

.subtitle {
  /* 缩到 13px，避免压住背景图下半部分的食材元素（月饼/生肉/莲藕等） */
  font-size: 13px;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.5;
  margin-top: var(--space-3);
}
</style>
