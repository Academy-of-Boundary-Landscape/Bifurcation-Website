<script setup lang="ts">
import { NModal, NButton } from 'naive-ui'
import { ref, onBeforeUnmount } from 'vue'

const props = defineProps<{
  isDirty: boolean
}>()

const emits = defineEmits(['confirm', 'cancel'])

const showModal = ref(false)

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
    @positive-click="() => { emits('confirm'); showModal.value = false; }"
    @negative-click="() => { emits('cancel'); showModal.value = false; }"
  >
    <template #action>
      <n-button type="primary" @click="() => { emits('confirm'); showModal.value = false; }">保存草稿</n-button>
      <n-button @click="() => { emits('cancel'); showModal.value = false; }">放弃离开</n-button>
    </template>
  </n-modal>
</template>
