<script setup lang="ts">
import { NModal, NButton } from 'naive-ui'
</script>

<template>
  <n-modal 
    v-model:show="show" 
    preset="dialog"
    title="{{ title }}"
    :content="content"
    @positive-click="$emit('confirm')"
    @negative-click="$emit('cancel')"
  >
    <template #action>
      <n-button type="primary" @click="$emit('confirm')">{{ confirmText }}</n-button>
      <n-button @click="$emit('cancel')">{{ cancelText }}</n-button>
    </template>
  </n-modal>
</template>

<script lang="ts">
export default {
  name: 'ConfirmDialog',
  props: {
    show: {
      type: Boolean,
      required: true,
    },
    title: {
      type: String,
      default: '确认操作',
    },
    content: {
      type: String,
      default: '确定要执行此操作吗？',
    },
    confirmText: {
      type: String,
      default: '确定',
    },
    cancelText: {
      type: String,
      default: '取消',
    }
  },
  emits: ['confirm', 'cancel']
}
</script>