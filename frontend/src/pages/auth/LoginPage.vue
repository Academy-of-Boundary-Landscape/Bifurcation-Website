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
      <section class="auth-copy">
        <p class="eyebrow">Identity Gateway</p>
        <h1>以统一身份进入分岔视界</h1>
        <p class="lead">
          登录、注册与密码找回都交给 Casdoor 处理。进入本站之后，日常权限校验仍然使用本站后端签发的本地会话。
        </p>
        <div class="copy-lines">
          <span>SSO 域名</span>
          <strong>auth.secret-sealing.club</strong>
        </div>
      </section>

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
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 24px;
}

.auth-copy,
.auth-panel {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(8, 8, 8, 0.82);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
}

.auth-copy {
  padding: 40px;
  color: #f5f5f5;
}

.eyebrow {
  margin: 0 0 18px;
  font-size: 12px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.48);
}

.auth-copy h1 {
  margin: 0;
  font-size: clamp(36px, 6vw, 72px);
  line-height: 1.05;
  letter-spacing: 0.04em;
}

.lead {
  max-width: 40rem;
  margin: 24px 0 0;
  color: rgba(255, 255, 255, 0.68);
  line-height: 1.85;
}

.copy-lines {
  display: inline-grid;
  gap: 8px;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.74);
}

.copy-lines span {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.44);
}

.auth-panel {
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
  .auth-grid {
    grid-template-columns: 1fr;
  }

  .auth-copy,
  .auth-panel {
    padding: 28px;
  }
}
</style>
