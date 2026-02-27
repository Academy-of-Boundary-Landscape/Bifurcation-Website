<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import { NButton, type ButtonProps } from 'naive-ui'

interface Props {
  accent?: 'violet' | 'blue' | 'green'
  ghost?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  accent: 'violet',
  ghost: false,
})

const attrs = useAttrs()

const mergedType = computed<ButtonProps['type']>(() => {
  if (attrs.type) {
    return attrs.type as ButtonProps['type']
  }
  return props.ghost ? 'default' : 'primary'
})

const accentClass = computed(() => `app-btn--${props.accent}`)
</script>

<template>
  <NButton
    v-bind="$attrs"
    class="app-btn"
    :class="[accentClass, { 'app-btn--ghost': ghost }]"
    :type="mergedType"
  >
    <slot />
  </NButton>
</template>

<style scoped>
.app-btn {
  position: relative;
  overflow: hidden;
  border-radius: 0 !important;
  border-width: 1px !important;
  border-color: rgba(255, 255, 255, 0.75) !important;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 600;
  transition: all 0.2s ease;
}

.app-btn::before {
  content: '';
  position: absolute;
  inset: 2px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  pointer-events: none;
}

.app-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent);
  opacity: 0.8;
  pointer-events: none;
}

.app-btn:hover {
  transform: translateY(-1px);
}

.app-btn--ghost {
  background: transparent !important;
}

.app-btn--violet {
  box-shadow:
    inset 0 0 0 1px rgba(124, 58, 237, 0.52),
    0 0 0 1px rgba(124, 58, 237, 0.22);
}

.app-btn--violet:hover {
  box-shadow:
    inset 0 0 0 1px rgba(124, 58, 237, 0.62),
    0 0 16px rgba(124, 58, 237, 0.4);
}

.app-btn--blue {
  box-shadow:
    inset 0 0 0 1px rgba(59, 130, 246, 0.52),
    0 0 0 1px rgba(59, 130, 246, 0.22);
}

.app-btn--blue:hover {
  box-shadow:
    inset 0 0 0 1px rgba(59, 130, 246, 0.64),
    0 0 16px rgba(59, 130, 246, 0.36);
}

.app-btn--green {
  box-shadow:
    inset 0 0 0 1px rgba(34, 197, 94, 0.5),
    0 0 0 1px rgba(34, 197, 94, 0.22);
}

.app-btn--green:hover {
  box-shadow:
    inset 0 0 0 1px rgba(34, 197, 94, 0.64),
    0 0 16px rgba(34, 197, 94, 0.34);
}
</style>
