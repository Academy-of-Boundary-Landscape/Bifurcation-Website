<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar, NDivider, NInput, NForm, NFormItem, NSelect } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref, onBeforeUnmount } from 'vue'
import type { StoryNodeRead, StoryNodeCreate } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, post } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const bookId = computed(() => Number(route.params.bookId))
const parentId = computed(() => Number(route.query.parentId))
const mode = computed(() => route.query.mode as 'continue' | 'branch')

// 获取父节点信息
const { data: parentNode, isLoading: isParentLoading } = useQuery<StoryNodeRead>({
  queryKey: ['story-node', parentId],
  queryFn: () => get<StoryNodeRead>(`/story/node/${parentId.value}`),
  enabled: !!parentId.value,
})

// 获取当前用户信息
const { data: currentUser } = useQuery({
  queryKey: ['auth-me'],
  queryFn: () => get('/auth/me'),
})

// 表单数据
const formData = ref<StoryNodeCreate>({
  book_id: bookId.value,
  parent_id: parentId.value || undefined,
  title: '',
  content: '',
  branch_name: '',
  zone: 'short',
})

// 字数统计
const contentLength = computed(() => formData.value.content.length)

// 草稿保存
const saveDraft = () => {
  if (parentId.value) {
    const draftKey = `draft_${bookId.value}_${parentId.value}_${mode.value}`
    localStorage.setItem(draftKey, JSON.stringify(formData.value))
  }
}

// 检查是否有未保存的草稿
const loadDraft = () => {
  if (parentId.value) {
    const draftKey = `draft_${bookId.value}_${parentId.value}_${mode.value}`
    const savedDraft = localStorage.getItem(draftKey)
    if (savedDraft) {
      try {
        const draft = JSON.parse(savedDraft)
        Object.assign(formData.value, draft)
      } catch (e) {
        console.error('加载草稿失败:', e)
      }
    }
  }
}

// 加载草稿
loadDraft()

// 提交创作
const { mutate: createNode, isPending: isCreating } = useMutation({
  mutationFn: () => post<{id: number}>('/story/node', formData.value),
  onSuccess: (data) => {
    message.success('创作提交成功，等待审核')
    // 清除草稿
    if (parentId.value) {
      const draftKey = `draft_${bookId.value}_${parentId.value}_${mode.value}`
      localStorage.removeItem(draftKey)
    }
    // 跳转到节点详情页
    router.push({ name: 'story-node', params: { nodeId: data.id } })
  },
  onError: (error) => {
    message.error('创作提交失败，请重试')
    console.error('提交失败:', error)
  }
})

function handleBack() {
  router.back()
}

// 离开前检查
onBeforeUnmount(() => {
  if (contentLength.value > 0) {
    const shouldSave = confirm('您有未保存的内容，是否保存为草稿？')
    if (shouldSave) {
      saveDraft()
    }
  }
})

function handleSubmit() {
  if (!formData.value.content.trim()) {
    message.error('内容不能为空')
    return
  }
  
  if (contentLength.value < 50) {
    message.warning('内容过短，建议至少50字')
  }
  
  createNode()
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <n-spin :show="isParentLoading">
      <n-space vertical :size="24">
        <!-- 前文摘要区 -->
        <n-card v-if="parentNode" class="bg-#1a1a1a border-#2a2a2a">
          <template #header>
            <h2 class="text-xl font-bold text-white">前文摘要</h2>
          </template>
          
          <div class="flex items-center gap-3 mb-4">
            <n-avatar :size="32">
              {{ parentNode.author?.username?.charAt(0).toUpperCase() }}
            </n-avatar>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ parentNode.title || parentNode.branch_name || '无标题' }}</h3>
              <p class="text-#666666">作者: {{ parentNode.author?.username }} | {{ new Date(parentNode.created_at).toLocaleDateString('zh-CN') }}</p>
            </div>
          </div>
          
          <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
            {{ parentNode.content.substring(0, 300) }}{{ parentNode.content.length > 300 ? '...' : '' }}
          </div>
          
          <div class="mt-4 pt-4 border-t border-#2a2a2a flex justify-end">
            <RouterLink 
              :to="`/story/node/${parentNode.id}`" 
              class="text-#8b5cf6 hover:underline"
            >
              查看完整前文 →
            </RouterLink>
          </div>
        </n-card>

        <!-- 创作类型说明 -->
        <n-card class="bg-#1a1a1a border-#2a2a2a">
          <template #header>
            <h2 class="text-xl font-bold text-white">{{ mode === 'continue' ? '续写创作' : '新分支创作' }}</h2>
          </template>
          
          <div class="space-y-4">
            <div v-if="mode === 'continue'" class="text-#d9d9d9">
              <p>您正在对「{{ parentNode?.title || parentNode?.branch_name || '该节点' }}」进行直接续写。</p>
              <p>请延续原有风格和设定，保持故事连贯性。</p>
            </div>
            
            <div v-else class="text-#d9d9d9">
              <p>您正在从「{{ parentNode?.title || parentNode?.branch_name || '该节点' }}」创建一个新的世界线分支。</p>
              <p>请填写分支名称，并创作新的内容，开启不同的可能性。</p>
            </div>
            
            <div class="bg-#2a2a2a p-4 rounded-lg">
              <h3 class="text-lg font-semibold text-white mb-2">创作要求</h3>
              <ul class="list-disc pl-5 space-y-1 text-#666666">
                <li>内容需符合世界观设定</li>
                <li>建议字数：50-2000字</li>
                <li>禁止包含违法不良信息</li>
              </ul>
            </div>
          </div>
        </n-card>

        <!-- 编辑器主体 -->
        <n-card class="bg-#1a1a1a border-#2a2a2a">
          <template #header>
            <h2 class="text-xl font-bold text-white">创作内容</h2>
          </template>
          
          <div class="space-y-6">
            <div v-if="mode === 'branch'">
              <n-form-item label="分支名称" required>
                <n-input 
                  v-model:value="formData.branch_name" 
                  placeholder="例如：平行世界的相遇"
                  class="w-full"
                />
              </n-form-item>
            </div>
            
            <n-form-item label="标题（可选）">
              <n-input 
                v-model:value="formData.title" 
                placeholder="为您的创作添加一个标题"
                class="w-full"
              />
            </n-form-item>
            
            <n-form-item label="正文内容" required>
              <n-input 
                v-model:value="formData.content" 
                type="textarea"
                placeholder="开始您的创作..."
                :rows="12"
                class="w-full"
              />
              <div class="flex justify-between mt-2 text-sm text-#666666">
                <span>字数: {{ contentLength }}</span>
                <span v-if="contentLength < 50" class="text-yellow-400">建议至少50字</span>
                <span v-else-if="contentLength > 2000" class="text-red-400">超过2000字</span>
              </div>
            </n-form-item>
          </div>
        </n-card>

        <!-- 提交区 -->
        <n-card class="bg-#1a1a1a border-#2a2a2a">
          <div class="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div class="text-#666666">
              <p>您的创作将进入审核流程，通过后即可发布</p>
              <p class="text-sm">草稿会自动保存，您可以随时返回继续创作</p>
            </div>
            
            <n-space>
              <n-button @click="handleBack" size="large">
                返回
              </n-button>
              <n-button 
                type="primary" 
                size="large"
                @click="handleSubmit"
                :loading="isCreating"
                :disabled="isCreating"
              >
                {{ mode === 'continue' ? '提交续写' : '提交分支创作' }}
              </n-button>
            </n-space>
          </div>
        </n-card>
      </n-space>
    </n-spin>
  </div>
</template>
