<script setup lang="ts">
import { NButton, NCard } from 'naive-ui'
import { useRoute } from 'vue-router'
import { ref } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { handleError } from '@/utils/error-handler'

const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')

async function handleSsoLogin() {
  loading.value = true
  errorMessage.value = ''
  try {
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/books'
    await authStore.beginSsoLogin(redirect)
  } catch (error) {
    handleError(error, '获取 SSO 登录地址失败')
    errorMessage.value = '获取 SSO 登录地址失败'
    loading.value = false
  } finally {
    if (errorMessage.value) {
      loading.value = false
    }
  }
}
</script>

<template>
  <div class="auth-entry-page">
    <div class="auth-grid">
      <n-card class="auth-panel" :bordered="false">
        <div class="panel-head">
          <h2>登录 / 注册</h2>
          <p>通过统一身份系统完成认证，再换取本站会话。</p>
        </div>

        <n-button
          type="primary"
          size="large"
          block
          :loading="loading"
          :disabled="loading"
          @click="handleSsoLogin"
        >
          使用 SSO 继续
        </n-button>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

        <div class="panel-note">
          <span>回调页</span>
          <code>/auth/callback</code>
        </div>
      </n-card>
    </div>
  </div>
</template>

<style scoped>
.auth-entry-page {
  min-height: 100vh;
  padding: 32px 20px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 15% 15%, rgba(255, 255, 255, 0.08), transparent 24%),
    radial-gradient(circle at 85% 20%, rgba(255, 255, 255, 0.05), transparent 20%),
    linear-gradient(160deg, #020202 0%, #111111 55%, #050505 100%);
}

.auth-grid {
  width: min(460px, 100%);
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.auth-panel {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(8, 8, 8, 0.82);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  display: grid;
  gap: 24px;
  align-content: center;
  padding: 32px;
}

.panel-head h2 {
  margin: 0;
  font-size: 28px;
  color: #ffffff;
}

.panel-head p {
  margin: 12px 0 0;
  color: rgba(255, 255, 255, 0.58);
  line-height: 1.8;
}

.error-message {
  margin: 0;
  color: #ffb4b4;
  line-height: 1.7;
}

.panel-note {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.52);
}

.panel-note code {
  color: rgba(255, 255, 255, 0.88);
}

@media (max-width: 900px) {
  .auth-panel {
    padding: 28px;
  }
}
</style>
