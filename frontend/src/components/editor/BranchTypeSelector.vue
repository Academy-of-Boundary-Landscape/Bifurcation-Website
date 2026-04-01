<script setup lang="ts">
import { NSelect, NTag } from 'naive-ui'
import { h } from 'vue'

const props = defineProps<{
  modelValue: string
}>()

const emits = defineEmits(['update:modelValue'])

// 分支类型选项
const branchTypes = [
  { value: 'long', label: '长篇', color: '#3b82f6' },
  { value: 'short', label: '短篇', color: '#10b981' }
]

function handleSelect(value: string) {
  emits('update:modelValue', value)
}
</script>

<template>
  <div class="flex items-center gap-2">
    <span class="text-#666666">区域类型:</span>
    
    <n-select 
      v-model:value="props.modelValue" 
      :options="branchTypes"
      @update:value="handleSelect"
      size="small"
      class="w-32"
      :render-tag="(option) => {
        return h(NTag, {
          type: 'default',
          size: 'small',
          style: `background-color: ${option.color}1a; color: ${option.color}; border-color: ${option.color}4d`
        }, () => option.label)
      }"
    />
  </div>
</template>
