<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'

const props = defineProps<{
  isSubmitting: boolean
  canSubmit: boolean
}>()

const emits = defineEmits(['submit', 'cancel', 'preview'])

function handlePreview() {
  emits('preview')
}
</script>

<template>
  <div class="flex justify-between items-center p-4 border-t border-#2a2a2a bg-#1a1a1a">
    <div class="flex gap-2">
      <n-button 
        type="default" 
        @click="$emit('cancel')"
      >
        取消
      </n-button>
      <n-button 
        type="default" 
        @click="handlePreview"
      >
        预览
      </n-button>
    </div>
    
    <n-button 
      type="primary" 
      :loading="props.isSubmitting"
      :disabled="!props.canSubmit || props.isSubmitting"
      @click="$emit('submit')"
    >
      {{ props.isSubmitting ? '提交中...' : '提交创作' }}
    </n-button>
  </div>
</template>