<script setup lang="ts">
/**
 * 图片中转页（上传中）
 * 来源：docs/Design.md §4.3
 * 流程：Home 选图 → 跳到此页 → 模拟上传 → 点击"发送给开饭" → /loading
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import TopBar from '@/components/TopBar.vue'
import { useDishStore } from '@/stores/dish'

const router = useRouter()
const dishStore = useDishStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const timers: number[] = []

/* === 计算：上传进度与按钮可用性 === */
const allDone = computed(() => dishStore.allImagesUploaded)
const hasAny = computed(() => dishStore.uploadedImages.length > 0)

/* === 模拟上传动画（每张图 200ms +5%） === */
function startMockUpload() {
  dishStore.uploadedImages.forEach((img, idx) => {
    if (img.status === 'done') return
    const t = window.setInterval(() => {
      const target = dishStore.uploadedImages.find((i) => i.id === img.id)
      if (!target) return
      const next = Math.min(100, target.progress + 5)
      if (next >= 100) {
        dishStore.updateImageStatus(img.id, 'done', 100)
        window.clearInterval(t)
      } else {
        dishStore.updateImageStatus(img.id, 'uploading', next)
      }
    }, 200)
    // 错开启动，避免所有图同时跑
    const delay = window.setTimeout(() => { /* noop, timer handles itself */ }, idx * 200)
    timers.push(t, delay)
  })
}

onMounted(() => {
  // 进入页面如果一张图都没有，回到首页
  if (!hasAny.value) {
    router.replace({ name: 'home' })
    return
  }
  startMockUpload()
})

onUnmounted(() => {
  timers.forEach((id) => {
    window.clearInterval(id)
    window.clearTimeout(id)
  })
})

/* === 交互：添加图片 === */
function onAddClick() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) return

  // 校验
  if (dishStore.uploadedImages.length + files.length > 5) {
    alert('最多 5 张图片哦～')
    input.value = ''
    return
  }
  const oversized = files.find((f) => f.size > 10 * 1024 * 1024)
  if (oversized) {
    alert('图片超过 10MB，请重新选择')
    input.value = ''
    return
  }

  dishStore.addImages(files)
  // 新加入的图继续走 mock 上传
  startMockUpload()
  input.value = ''
}

/* === 交互：删除单张图 === */
function onRemove(id: string) {
  dishStore.removeImage(id)
  if (dishStore.uploadedImages.length === 0) {
    router.replace({ name: 'home' })
  }
}

/* === 交互：发送给开饭 === */
function onSend() {
  if (!allDone.value) return
  router.push({ name: 'loading' })
}
</script>

<template>
  <div class="upload page">
    <!-- 顶部固定栏 -->
    <TopBar title="已上传图片" />

    <!-- 瀑布流图片列表 -->
    <main v-if="hasAny" class="image-grid">
      <div
        v-for="img in dishStore.uploadedImages"
        :key="img.id"
        class="image-card"
      >
        <img class="image" :src="img.url" alt="" aria-hidden="true" />

        <!-- 三个点菜单 -->
        <button
          class="menu-btn"
          type="button"
          aria-label="更多操作"
          @click="onRemove(img.id)"
        >
          <span aria-hidden="true">⋮</span>
        </button>

        <!-- 上传中遮罩 -->
        <div
          v-if="img.status === 'pending' || img.status === 'uploading'"
          class="upload-mask"
          aria-live="polite"
        >
          <!-- 圆形进度环（CSS conic-gradient） -->
          <div
            class="ring"
            :style="{ '--p': img.progress }"
            role="progressbar"
            :aria-valuenow="img.progress"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div class="ring-inner">
              <span class="percent">{{ img.progress }}%</span>
            </div>
          </div>
          <span class="mask-text">上传中</span>
          <!-- 底部进度条 -->
          <div class="bar">
            <div class="bar-fill" :style="{ width: img.progress + '%' }" />
          </div>
        </div>
      </div>
    </main>

    <!-- 底部固定操作区 -->
    <footer class="bottom-bar">
      <button
        class="btn btn-secondary"
        type="button"
        @click="onAddClick"
      >
        <span class="plus" aria-hidden="true">+</span>
        添加图片
      </button>
      <button
        class="btn btn-primary"
        type="button"
        :disabled="!allDone"
        @click="onSend"
      >
        发送给开饭
      </button>
    </footer>

    <!-- 隐藏的文件选择器 -->
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
.upload {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-bg);
}

/* === 瀑布流：双列等宽 === */
.image-grid {
  flex: 1;
  column-count: 2;
  column-gap: var(--space-2); /* 8px */
  padding: var(--space-4); /* 16px 上下左右 */
  /* 给底部按钮区留出空间，避免最后一张被遮挡 */
  padding-bottom: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-4));
}

.image-card {
  position: relative;
  display: inline-block;
  width: 100%;
  margin-bottom: var(--space-2); /* 8px */
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-bg-tertiary);
  break-inside: avoid;
}

.image {
  display: block;
  width: 100%;
  height: auto;
  object-fit: cover;
}

/* === 三个点菜单（暂作删除入口） === */
.menu-btn {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  border-radius: var(--radius-full);
  font-size: 18px;
  line-height: 1;
  transition: opacity var(--duration-fast) var(--ease-default);
}

.menu-btn:active {
  opacity: 0.7;
}

/* === 上传中遮罩 === */
.upload-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  background: rgba(42, 37, 32, 0.5);
}

.ring {
  --p: 0;
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: conic-gradient(
    var(--color-bg) calc(var(--p) * 1%),
    rgba(255, 255, 255, 0.2) 0
  );
  /* 视觉微调：让环有 4px 厚度感 */
  padding: 4px;
}

.ring-inner {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-full);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.percent {
  font-size: var(--text-body-lg); /* 24px（Design §4.3.2 规范） */
  font-weight: var(--font-medium);
  color: var(--color-bg);
}

.mask-text {
  font-size: var(--text-caption);
  color: var(--color-bg);
}

.bar {
  position: absolute;
  left: var(--space-3);
  right: var(--space-3);
  bottom: var(--space-3);
  height: 3px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--color-bg);
  transition: width 200ms var(--ease-default);
}

/* === 底部固定操作区 === */
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-fixed);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: calc(var(--size-tabbar) + var(--safe-bottom) + var(--space-3));
  padding: 0 var(--space-4);
  padding-bottom: calc(var(--safe-bottom) + var(--space-3));
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
}

.btn {
  height: var(--size-button-lg); /* 56px */
  padding: 0 var(--space-6);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  font-weight: var(--font-medium);
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.btn:active {
  opacity: 0.85;
  transform: scale(0.98);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-secondary {
  flex: 0 0 30%;
  background: var(--color-bg);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

.plus {
  font-size: 20px;
  line-height: 1;
  transform: translateY(-1px);
}

.btn-primary {
  flex: 1;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
}

/* === 隐藏的 file input === */
.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}
</style>