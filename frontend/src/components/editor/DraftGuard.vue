<script setup lang="ts">
import { NModal, NButton } from 'naive-ui'
import { ref, onBeforeUnmount } from 'vue'

const props = defineProps<{
  isDirty: boolean
}>()

const emits = defineEmits(['confirm', 'cancel'])

const showModal = ref(false)

function handleConfirm() {
  emits('confirm')
  showModal.value = false
}

function handleCancel() {
  emits('cancel')
  showModal.value = false
}

// 页面离开前检查
onBeforeUnmount(() => {
  if (props.isDirty) {
    const shouldSave = confirm('您有未保存的内容，是否保存为草稿？')
    if (shouldSave) {
      emits('confirm')
    }
  }
})
</script>

<template>
  <n-modal 
    v-model:show="showModal" 
    preset="dialog"
    title="离开前确认"
    :content="'您有未保存的内容，是否保存为草稿？'"
    @positive-click="handleConfirm"
    @negative-click="handleCancel"
  >
    <template #action>
      <n-button type="primary" @click="handleConfirm">保存草稿</n-button>
      <n-button @click="handleCancel">放弃离开</n-button>
    </template>
  </n-modal>
</template>
