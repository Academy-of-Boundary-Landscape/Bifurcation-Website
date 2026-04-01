<script setup lang="ts">
import { NCard, NButton, NSpace, NInput, NSelect, NFormItem, NForm, NIcon } from 'naive-ui'
import { ref, computed, watch } from 'vue'
import type { StoryNodeCreate } from '@/types/models'

const props = defineProps<{
  modelValue: StoryNodeCreate
  mode: 'continue' | 'branch'
}>()

const emits = defineEmits(['update:modelValue', 'submit', 'cancel'])

const formData = ref<StoryNodeCreate>(props.modelValue)

// 监听父组件传入的值变化
watch(() => props.modelValue, (newVal) => {
  formData.value = newVal
})

// 监听本地表单变化并同步到父组件
watch(formData, (newVal) => {
  emits('update:modelValue', newVal)
}, { deep: true })

// 字数统计
const contentLength = computed(() => formData.value.content.length)

function handleSubmit() {
  if (!formData.value.content.trim()) {
    alert('内容不能为空')
    return
  }
  
  if (contentLength.value < 50) {
    alert('内容过短，建议至少50字')
  }
  
  emits('submit', formData.value)
}
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <h2 class="text-xl font-bold text-white">
        {{ mode === 'continue' ? '续写创作' : '新分支创作' }}
      </h2>
      <p class="text-#666666 text-sm mt-1">
        {{ mode === 'continue' ? '在现有节点上进行延续创作' : '从当前节点开启新的世界线分支' }}
      </p>
    </template>
    
    <n-form :model="formData" :show-feedback="true">
      <!-- 分支名称（仅分支模式） -->
      <n-form-item v-if="mode === 'branch'" label="分支名称" required>
        <n-input 
          v-model:value="formData.branch_name" 
          placeholder="例如：平行世界的相遇"
          class="w-full"
        />
      </n-form-item>
      
      <!-- 标题 -->
      <n-form-item label="标题（可选）">
        <n-input 
          v-model:value="formData.title" 
          placeholder="为您的创作添加一个标题"
          class="w-full"
        />
      </n-form-item>
      
      <!-- 内容 -->
      <n-form-item label="正文内容" required>
        <n-input
          type="textarea"
          v-model:value="formData.content" 
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
      
      <!-- 区域选择 -->
      <n-form-item label="区域类型" required>
        <n-select 
          v-model:value="formData.zone" 
          :options="[
            { label: '长篇', value: 'long' },
            { label: '短篇', value: 'short' }
          ]"
          placeholder="选择创作区域"
          class="w-full"
        />
      </n-form-item>
    </n-form>
    
    <div class="mt-6 flex justify-end gap-3">
      <n-button @click="$emit('cancel')">
        取消
      </n-button>
      <n-button type="primary" @click="handleSubmit">
        {{ mode === 'continue' ? '提交续写' : '提交分支创作' }}
      </n-button>
    </div>
  </n-card>
</template>
