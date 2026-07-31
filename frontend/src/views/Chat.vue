<script setup lang="ts">
/**
 * 输入页（图片 + 文字）
 * 来源：用户需求（2026-07-29）—— 对话式输入替代 /upload 中转页
 *
 * 布局：
 *   [TopBar：图片和文字都行]
 *   [大上传区：正方形 + 按钮，支持预览已选图]
 *   [底部输入区：文字输入框 + 发送按钮]
 *
 * 行为：
 *   - 点上传区 → 唤起系统相册（多选）
 *   - 选完图 → 在上传区显示缩略图，可单独删除
 *   - 点发送 → 写入 store → 跳转 /loading（AI 生成菜谱）
 *   - 发送按钮禁用态：输入框为空 + 无图
 *
 * 设计参考：ui-ux-pro-max（Block-based, Warm, Single-task focus）
 * Token 映射：见 styles/tokens.css + Design.md §2
 */
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import chatBg from '@/assets/chat-bg.jpg'
import { useDishStore } from '@/stores/dish'

const router = useRouter()
const dishStore = useDishStore()

/* === 上传区状态 === */
interface PendingImage {
  id: string
  url: string
  file: File
}

const pendingImages = ref<PendingImage[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

/* === 文字输入 === */
const text = ref('')

const canSend = computed(
  () => text.value.trim().length > 0 || pendingImages.value.length > 0,
)

/* === 唤起相册 === */
function onUploadClick() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) return

  // 数量限制
  const remaining = 5 - pendingImages.value.length
  if (files.length > remaining) {
    alert(`最多还能选 ${remaining} 张哦～`)
    input.value = ''
    return
  }

  // 大小限制
  const oversized = files.find((f) => f.size > 10 * 1024 * 1024)
  if (oversized) {
    alert('图片超过 10MB，请重新选择')
    input.value = ''
    return
  }

  files.forEach((file) => {
    pendingImages.value.push({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      url: URL.createObjectURL(file),
      file,
    })
  })

  input.value = ''
}

function removeImage(id: string) {
  pendingImages.value = pendingImages.value.filter((img) => img.id !== id)
}

/* === 退出 === */
function onExit() {
  router.push({ name: 'home' })
}

/* === 发送 === */
function onSend() {
  if (!canSend.value) return

  // 文字写入 store（传给后端 LLM）
  dishStore.setText(text.value.trim())

  // 图片写入 store
  if (pendingImages.value.length > 0) {
    dishStore.addImages(pendingImages.value.map((i) => i.file))
  }

  // 跳转到加载页（生成菜谱）
  router.push({ name: 'loading' })
}
</script>

<template>
  <div class="chat page" :style="{ backgroundImage: `url(${chatBg})` }">
    <!-- 透明头部：仅退出按钮 -->
    <header class="chat-header">
      <button
        class="exit-btn"
        type="button"
        aria-label="退出"
        @click="onExit"
      >
        <span aria-hidden="true">‹</span>
      </button>
    </header>

    <!-- 上传区：屏幕中央的大正方形 -->
    <main class="upload-area">
      <button
        class="upload-square"
        :class="{ filled: pendingImages.length > 0 }"
        type="button"
        aria-label="上传买菜截图或菜品图片"
        @click="onUploadClick"
      >
        <!-- 空态：+ 号 + 提示 -->
        <template v-if="pendingImages.length === 0">
          <span class="plus-icon" aria-hidden="true">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M24 12v24M12 24h24"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
              />
            </svg>
          </span>
          <span class="upload-label">买菜截图也行</span>
          <span class="upload-hint">支持 1-5 张 · JPG / PNG · ≤10MB</span>
        </template>

        <!-- 已选图：水平排开叠放（每张错位 + 旋转，类似扑克牌扇形展开） -->
        <template v-else>
          <div class="thumb-stack">
            <div
              v-for="(img, idx) in pendingImages.slice(0, 3)"
              :key="img.id"
              class="thumb-card"
              :style="{
                zIndex: pendingImages.length - idx,
                marginLeft: idx === 0 ? '0' : '-28px',
                transform: `rotate(${idx * -4}deg)`,
              }"
            >
              <img :src="img.url" alt="" />
              <button
                class="thumb-remove"
                type="button"
                aria-label="移除图片"
                @click.stop="removeImage(img.id)"
              >
                ×
              </button>
              <!-- 第 3 张显示 +N -->
              <span v-if="idx === 2 && pendingImages.length > 3" class="thumb-more">
                +{{ pendingImages.length - 3 }}
              </span>
            </div>
          </div>
          <span class="upload-label">
            已选 {{ pendingImages.length }} 张
            <span class="upload-tips">· 点击继续添加</span>
          </span>
        </template>
      </button>
    </main>

    <!-- 底部输入区：文字输入 + 发送按钮 -->
    <footer class="input-bar">
      <textarea
        v-model="text"
        class="text-input"
        rows="1"
        placeholder="告诉我 你有什么菜"
        enterkeyhint="send"
        @keydown.enter.exact.prevent="onSend"
      />
      <button
        class="send-btn"
        type="button"
        :disabled="!canSend"
        @click="onSend"
      >
        发送
      </button>
    </footer>

    <!-- 隐藏的 file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      multiple
      class="file-input"
      aria-hidden="true"
      @change="onFileChange"
    />
  </div>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  background-color: var(--color-bg-secondary);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* === 透明头部：仅退出按钮 === */
.chat-header {
  position: absolute;
  top: var(--safe-top);
  left: 0;
  right: 0;
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

/* === 上传区 === */
.upload-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6) var(--space-4);
  /* 给顶部退出按钮 + 安全区留出空间 */
  padding-top: calc(var(--safe-top) + var(--size-topbar) + var(--space-6));
}

.upload-square {
  /* 缩小：左右各留 ~64px，max-width 256px（原 320px） */
  width: calc(100vw - var(--space-16) * 2);
  max-width: 16rem; /* 256px */
  min-width: 12rem; /* 192px */
  aspect-ratio: 1 / 1;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);

  /* 透明背景 + 灰色边框，让背景图透出 */
  background: transparent;
  border: 2px dashed var(--color-border-strong);
  border-radius: var(--radius-xl); /* 16px */
  color: var(--color-text-primary);

  transition:
    background var(--duration-fast) var(--ease-default),
    border-color var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.upload-square:active {
  background: rgba(42, 37, 32, 0.04); /* 极浅按下反馈 */
  transform: scale(0.98);
}

.upload-square.filled {
  /* 已选图：实线 + 白底，让缩略图清晰 */
  background: var(--color-bg);
  border-style: solid;
  border-color: var(--color-border-strong);
}

.upload-square.filled:active {
  background: var(--color-primary-bg);
}

.plus-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: var(--color-primary);
}

.plus-icon svg {
  width: 100%;
  height: 100%;
}

.upload-label {
  font-size: var(--text-body); /* 18px */
  font-weight: var(--font-medium);
  color: var(--color-text-primary);
}

.upload-hint {
  font-size: var(--text-caption); /* 14px */
  color: var(--color-text-tertiary);
  text-align: center;
}

/* === 缩略图叠放（已选图，水平排开 + 错位 + 旋转） === */
.thumb-stack {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2) 0;
  min-height: 110px;
}

.thumb-card {
  position: relative;
  width: 80px;
  height: 100px;
  flex: 0 0 auto;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-bg);
  box-shadow: var(--shadow-card);
  transition: transform var(--duration-fast) var(--ease-default);
}

.thumb-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 删除按钮：白底圆形 + 深色 × */
.thumb-remove {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-text-primary);
  font-size: 16px;
  line-height: 1;
  font-weight: var(--font-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  transition: transform var(--duration-fast) var(--ease-default);
}

.thumb-remove:active {
  transform: scale(0.9);
}

/* +N 蒙版 */
.thumb-more {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  color: var(--color-bg);
  font-size: var(--text-h3); /* 20px */
  font-weight: var(--font-semibold);
}

/* 已选 N 张 文字 */
.upload-tips {
  color: var(--color-text-tertiary);
  font-weight: var(--font-regular);
}

/* === 底部输入区 === */
.input-bar {
  display: flex;
  align-items: flex-end; /* 文字多行时按钮贴着底部 */
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  padding-bottom: calc(var(--safe-bottom) + var(--space-3));
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
  box-shadow: 0 -2px 12px rgba(42, 37, 32, 0.06); /* 向上阴影与背景图分层 */
}

.text-input {
  flex: 1;
  min-height: 44px;
  max-height: 120px;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  font-family: inherit;
  font-size: var(--text-body); /* 18px */
  color: var(--color-text-primary);
  line-height: 1.5;
  resize: none;
  outline: none;
  transition: background var(--duration-fast) var(--ease-default);
}

.text-input::placeholder {
  color: var(--color-text-tertiary);
}

.text-input:focus {
  background: var(--color-bg);
  box-shadow: inset 0 0 0 1px var(--color-border-strong);
}

.send-btn {
  flex: 0 0 auto;
  height: 44px;
  padding: 0 var(--space-5);
  border-radius: var(--radius-full);
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  font-size: var(--text-body-sm);
  font-weight: var(--font-medium);
  transition:
    background var(--duration-fast) var(--ease-default),
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.send-btn:active:not(:disabled) {
  opacity: 0.85;
  transform: scale(0.96);
}

.send-btn:disabled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-disabled);
  cursor: not-allowed;
}

/* === 隐藏 file input === */
.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

/* === 减少动效偏好 === */
@media (prefers-reduced-motion: reduce) {
  .upload-square,
  .send-btn {
    transition: none;
  }
}
</style>