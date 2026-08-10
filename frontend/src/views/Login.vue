<script setup lang="ts">
/**
 * 登录 / 注册 二合一页
 * 视觉：径向渐变背景（warm humanist）+ 玻璃面板 + 大品牌字「开饭」
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useDishStore } from '@/stores/dish'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const dishStore = useDishStore()

type Mode = 'login' | 'register'
const mode = ref<Mode>('login')

const username = ref('')
const password = ref('')
const password2 = ref('')
const submitting = ref(false)
const errorMsg = ref('')

const isRegister = computed(() => mode.value === 'register')
const redirectTarget = computed(() => {
  const r = route.query.redirect
  if (typeof r === 'string' && r.startsWith('/')) return r
  return '/mine'
})

onMounted(() => {
  if (auth.isAuthenticated) {
    router.replace(redirectTarget.value)
  }
})

function switchMode(next: Mode) {
  if (mode.value === next) return
  mode.value = next
  errorMsg.value = ''
  password.value = ''
  password2.value = ''
}

function validate(): string | null {
  const u = username.value.trim()
  if (u.length < 2) return '用户名至少 2 个字'
  if (u.length > 32) return '用户名最长 32 个字'
  if (password.value.length < 6) return '密码至少 6 位'
  if (password.value.length > 64) return '密码最长 64 位'
  if (isRegister.value && password.value !== password2.value) {
    return '两次密码不一致'
  }
  return null
}

async function onSubmit() {
  errorMsg.value = ''
  const v = validate()
  if (v) {
    errorMsg.value = v
    return
  }
  submitting.value = true
  try {
    if (isRegister.value) {
      await auth.register(username.value.trim(), password.value)
    } else {
      await auth.login(username.value.trim(), password.value)
    }
    try {
      await dishStore.loadRemoteHistory()
    } catch (e) {
      console.warn('拉取服务端历史失败', e)
    }
    router.replace(redirectTarget.value)
  } catch (e) {
    if (e instanceof ApiError) {
      errorMsg.value = e.message
    } else {
      errorMsg.value = '网络开小差了，重试一下'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login page">
    <!-- 径向渐变背景（沉浸） -->
    <div class="bg" aria-hidden="true">
      <!-- 装饰圆点 -->
      <div class="bg-dot bg-dot-1" />
      <div class="bg-dot bg-dot-2" />
      <div class="bg-dot bg-dot-3" />
    </div>

    <!-- 顶部品牌区 -->
    <header class="brand">
      <div class="brand-mark" aria-hidden="true">🍚</div>
      <h1 class="brand-title">开饭</h1>
      <p class="brand-subtitle">随时准备帮你做顿好的</p>
    </header>

    <!-- 玻璃面板 -->
    <main class="panel">
      <!-- tab 切换（带滑动指示条） -->
      <div class="tabs" role="tablist">
        <div
          class="tab-indicator"
          :class="{ right: isRegister }"
          aria-hidden="true"
        />
        <button
          type="button"
          class="tab"
          :class="{ active: !isRegister }"
          role="tab"
          :aria-selected="!isRegister"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          type="button"
          class="tab"
          :class="{ active: isRegister }"
          role="tab"
          :aria-selected="isRegister"
          @click="switchMode('register')"
        >
          注册
        </button>
      </div>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field-label">用户名</span>
          <input
            v-model="username"
            class="input"
            type="text"
            autocomplete="username"
            placeholder="2 - 32 个字"
            :disabled="submitting"
            maxlength="32"
          />
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="password"
            class="input"
            type="password"
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
            placeholder="6 - 64 位"
            :disabled="submitting"
            maxlength="64"
          />
        </label>

        <Transition name="slide-down">
          <label v-if="isRegister" class="field">
            <span class="field-label">再输入一次</span>
            <input
              v-model="password2"
              class="input"
              type="password"
              autocomplete="new-password"
              placeholder="再输入一次密码"
              :disabled="submitting"
              maxlength="64"
            />
          </label>
        </Transition>

        <Transition name="fade">
          <p v-if="errorMsg" class="error" role="alert">{{ errorMsg }}</p>
        </Transition>

        <button
          type="submit"
          class="submit-btn"
          :disabled="submitting"
        >
          {{ submitting ? '稍等…' : isRegister ? '注册并登录' : '登录' }}
        </button>

        <p class="hint">
          {{ isRegister ? '注册即视为同意开饭使用规则' : '未注册的账号会自动创建' }}
        </p>
      </form>
    </main>

    <footer class="footer">
      <router-link to="/" class="footer-link">
        <span>继续浏览</span>
        <span aria-hidden="true">→</span>
      </router-link>
    </footer>
  </div>
</template>

<style scoped>
.login {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: calc(var(--safe-top) + var(--space-12)) var(--space-6) var(--space-8);
  position: relative;
  overflow: hidden;
  background: var(--color-bg-secondary);
}

/* === 径向渐变 + 装饰圆点 === */
.bg {
  position: absolute;
  inset: 0;
  background: var(--bg-warm-radial);
  pointer-events: none;
  z-index: 0;
}

.bg-dot {
  position: absolute;
  border-radius: var(--radius-full);
  filter: blur(40px);
  opacity: 0.5;
}

.bg-dot-1 {
  width: 240px;
  height: 240px;
  top: -60px;
  left: -60px;
  background: rgba(255, 184, 136, 0.6);
}

.bg-dot-2 {
  width: 180px;
  height: 180px;
  bottom: 20%;
  right: -40px;
  background: rgba(123, 196, 127, 0.4);
}

.bg-dot-3 {
  width: 160px;
  height: 160px;
  bottom: -30px;
  left: 20%;
  background: rgba(255, 226, 198, 0.7);
}

.brand,
.panel,
.footer {
  position: relative;
  z-index: 1;
}

/* === 顶部品牌 === */
.brand {
  text-align: center;
  margin-bottom: var(--space-10);
}

.brand-mark {
  font-size: 48px;
  line-height: 1;
  margin-bottom: var(--space-3);
  filter: drop-shadow(0 4px 12px rgba(255, 122, 69, 0.2));
}

.brand-title {
  font-size: 36px;
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  letter-spacing: 8px;
  margin: 0;
  /* 微微字距收紧后展开，有"开饭开饭开饭"的呼吸感 */
  text-indent: 8px;
}

.brand-subtitle {
  margin: var(--space-3) 0 0;
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  letter-spacing: 1px;
}

/* === 玻璃面板 === */
.panel {
  width: 100%;
  max-width: 24rem;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-3xl);
  box-shadow: var(--shadow-card-lifted);
  padding: var(--space-6);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
}

/* === Tabs（带滑动指示条） === */
.tabs {
  display: flex;
  position: relative;
  border-bottom: 1px solid var(--color-divider);
  margin-bottom: var(--space-6);
}

.tab {
  flex: 1;
  height: 44px;
  background: transparent;
  font-size: var(--text-body);
  color: var(--color-text-tertiary);
  font-weight: var(--font-medium);
  position: relative;
  z-index: 1;
  transition: color var(--duration-fast) var(--ease-default);
}

.tab.active {
  color: var(--color-text-primary);
  font-weight: var(--font-semibold);
}

.tab-indicator {
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50%;
  height: 3px;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  transition: transform var(--duration-medium) var(--ease-spring);
}

.tab-indicator.right {
  transform: translateX(100%);
}

/* === 表单 === */
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-size: var(--text-caption);
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
  letter-spacing: 0.5px;
}

.input {
  height: 48px;
  padding: 0 var(--space-4);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  color: var(--color-text-primary);
  transition:
    border-color var(--duration-fast) var(--ease-default),
    box-shadow var(--duration-fast) var(--ease-default);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(255, 122, 69, 0.12);
}

.input::placeholder {
  color: var(--color-text-tertiary);
}

.input:disabled {
  opacity: 0.6;
}

/* === 错误提示 === */
.error {
  font-size: var(--text-body-sm);
  color: var(--color-error);
  background: rgba(231, 76, 60, 0.08);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin: 0;
  border-left: 3px solid var(--color-error);
}

/* === 主按钮 === */
.submit-btn {
  margin-top: var(--space-2);
  height: 52px;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: var(--radius-md);
  font-size: var(--text-body);
  font-weight: var(--font-semibold);
  letter-spacing: 4px;
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default);
}

.submit-btn:active:not(:disabled) {
  opacity: 0.85;
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.5;
}

.hint {
  text-align: center;
  font-size: var(--text-caption);
  color: var(--color-text-tertiary);
  margin: 0;
}

/* === Footer === */
.footer {
  margin-top: var(--space-8);
}

.footer-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-body-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: var(--space-2) var(--space-4);
  transition: color var(--duration-fast) var(--ease-default);
}

.footer-link:active {
  color: var(--color-text-primary);
}

/* === 动效 === */
.slide-down-enter-active,
.slide-down-leave-active {
  transition:
    opacity var(--duration-fast) var(--ease-default),
    transform var(--duration-fast) var(--ease-default),
    max-height var(--duration-normal) var(--ease-default);
  overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 80px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-default);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>