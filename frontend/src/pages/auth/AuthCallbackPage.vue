<script setup lang="ts">
import { NButton, NCard, NSpin } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { handleError } from '@/utils/error-handler'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const errorMessage = ref('')

async function finishSsoLogin() {
  const code = typeof route.query.code === 'string' ? route.query.code : ''
  const state = typeof route.query.state === 'string' ? route.query.state : ''
  const oauthError = typeof route.query.error === 'string' ? route.query.error : ''

  console.info('[SSO] auth callback page loaded', {
    href: window.location.href,
    origin: window.location.origin,
    hasCode: !!code,
    hasState: !!state,
    oauthError,
  })

  if (oauthError) {
    errorMessage.value = `SSO 登录失败: ${oauthError}`
    loading.value = false
    return
  }

  if (!code || !state) {
    errorMessage.value = '回调参数不完整，请重新发起登录'
    loading.value = false
    return
  }

  try {
    const response = await authStore.exchangeSsoCode(code, state)
    router.replace(response.redirect_to || '/books')
  } catch (error) {
    handleError(error)
    if (typeof error === 'object' && error !== null && 'response' in error) {
      const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
      errorMessage.value = detail || '登录交换失败，请稍后重试'
    } else {
      errorMessage.value = error instanceof Error ? error.message : '登录交换失败，请稍后重试'
    }
    loading.value = false
  }
}

onMounted(() => {
  void finishSsoLogin()
})
</script>

<template>
  <div class="auth-callback-page">
    <n-card class="callback-card" :bordered="false">
      <template v-if="loading">
        <div class="callback-state">
          <n-spin size="large" />
          <h1>正在接入身份</h1>
          <p>正在用 Casdoor 身份换取本站会话，请稍候。</p>
        </div>
      </template>
      <template v-else>
        <div class="callback-state">
          <h1>登录失败</h1>
          <p>{{ errorMessage }}</p>
          <n-button type="primary" @click="router.replace('/login')">返回登录页</n-button>
        </div>
      </template>
    </n-card>
  </div>
</template>

<style scoped>
.auth-callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 30%),
    linear-gradient(180deg, #050505 0%, #111111 100%);
}

.callback-card {
  width: min(100%, 520px);
  background: rgba(10, 10, 10, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 80px rgba(0, 0, 0, 0.45);
}

.callback-state {
  display: grid;
  gap: 16px;
  justify-items: center;
  text-align: center;
  color: rgba(255, 255, 255, 0.9);
  padding: 24px 12px;
}

.callback-state h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: 0.08em;
}

.callback-state p {
  margin: 0;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.7;
}
</style>
