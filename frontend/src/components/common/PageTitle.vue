<script setup lang="ts">
import { NText } from 'naive-ui'
</script>

<template>
  <div class="mb-6">
    <n-text class="text-2xl font-bold text-white">{{ title }}</n-text>
    <p v-if="description" class="text-#666666 mt-2">{{ description }}</p>
  </div>
</template>

<script lang="ts">
export default {
  name: 'PageTitle',
  props: {
    title: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      default: '',
    }
  }
}
</script>