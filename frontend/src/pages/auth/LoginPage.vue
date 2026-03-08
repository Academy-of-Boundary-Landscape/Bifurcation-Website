<script setup lang="ts">
import { NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert } from 'naive-ui'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'

const router = useRouter(
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')

const formData = ref({
  emailOrUsername: '',
  password: '',
})

const rules = {
  emailOrUsername: {
    required: true,
    message: '请输入邮箱或用户名',
    trigger: 'blur',
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur',
  },
}

async function handleLogin() {
  if (!formData.value.emailOrUsername || !formData.value.password) {
    message.error('请填写完整信息')
    return
  }
  
  loading.value = true
  errorMessage.value = ''
  
  try {
    await authStore.login(formData.value.emailOrUsername, formData.value.password)
