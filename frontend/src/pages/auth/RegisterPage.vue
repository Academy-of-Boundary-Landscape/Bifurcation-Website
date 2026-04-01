<script setup lang="ts">
import { NButton, NCard } from 'naive-ui'
import { useRoute } from 'vue-router'
import { ref } from 'vue'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')

async function handleSsoRegister() {
  loading.value = true
  errorMessage.value = ''
  try {
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/books'
    await authStore.beginSsoLogin(redirect)
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || error?.message || '获取 SSO 注册地址失败'
  } finally {
    if (errorMessage.value) {
      loading.value = false
    }
  }
}
</script>

<template>
  <div class="auth-register-page">
    <n-card class="register-panel" :bordered="false">
      <div class="register-copy">
        <p class="eyebrow">Create Identity</p>
        <h1>注册入口已切换到统一身份系统</h1>
        <p>
          账号创建、邮箱验证与密码找回不再由本站自己处理。点击下面的按钮后，将跳转到 Casdoor 完成注册或登录。
        </p>
      </div>

      <n-button
        type="primary"
        size="large"
        block
        :loading="loading"
        :disabled="loading"
        @click="handleSsoRegister"
      >
        前往 Casdoor
      </n-button>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

      <div class="register-note">
        <span>SSO 域名</span>
        <strong>auth.secret-sealing.club</strong>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.auth-register-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.04), transparent 35%),
    linear-gradient(180deg, #070707 0%, #131313 100%);
}

.register-panel {
  width: min(100%, 560px);
  display: grid;
  gap: 24px;
  padding: 36px;
  background: rgba(10, 10, 10, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 72px rgba(0, 0, 0, 0.42);
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.46);
}

.register-copy h1 {
  margin: 0;
  color: #ffffff;
  font-size: 34px;
  line-height: 1.2;
}

.register-copy p:last-child {
  margin: 16px 0 0;
  color: rgba(255, 255, 255, 0.64);
  line-height: 1.8;
}

.error-message {
  margin: 0;
  color: #ffb4b4;
}

.register-note {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.56);
}

@media (max-width: 640px) {
  .register-panel {
    padding: 28px;
  }

  .register-copy h1 {
    font-size: 28px;
  }
}
</style>
