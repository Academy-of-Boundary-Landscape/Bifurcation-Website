<script setup lang="ts">
import { NCard, NTag } from 'naive-ui'
import { RouterLink } from 'vue-router'
import AppButton from '@/components/common/AppButton.vue'

const quickLinks = [
  { title: '进入发现流', desc: '浏览全站最新发布的故事节点', to: '/discovery', accent: 'violet' as const },
  { title: '查看热门榜', desc: '按近期热度查看最受欢迎分支', to: '/trending', accent: 'blue' as const },
  { title: '浏览活动', desc: '选择故事活动并进入树状阅读', to: '/books', accent: 'green' as const },
]
</script>

<template>
  <section class="space-y-6">
    <NCard class="sci-panel! overflow-hidden">
      <div class="grid gap-6 md:grid-cols-[1.3fr_1fr] md:items-center">
        <div class="space-y-4">
          <NTag bordered type="info" size="small">TREE STORY · FUTURE FICTION</NTag>
          <h1 class="m-0 text-3xl md:text-5xl font-600 tracking-[0.08em] leading-tight">
            在黑色终端里，
            <span class="text-accent-violet">续写</span>
            属于你的分支。
          </h1>
          <p class="m-0 max-w-[60ch] text-text-muted leading-7">
            这里是一个协作式故事树平台。你可以沿着任意分支阅读、评论、点赞，并在合适的节点继续创作。
          </p>
          <div class="flex flex-wrap items-center gap-3 pt-2">
            <RouterLink to="/discovery">
              <AppButton accent="violet" size="large">开始探索</AppButton>
            </RouterLink>
            <RouterLink to="/story/write">
              <AppButton accent="green" ghost size="large">我要续写</AppButton>
            </RouterLink>
          </div>
        </div>

        <div class="sci-panel min-h-[220px] p-4 md:p-5 flex flex-col justify-between">
          <div class="text-sm tracking-[0.08em] uppercase text-text-muted">System Overview</div>
          <div class="grid grid-cols-2 gap-3">
            <div class="sci-panel p-3">
              <div class="text-xs text-text-muted uppercase">模式</div>
              <div class="mt-2 text-lg">Public</div>
            </div>
            <div class="sci-panel p-3">
              <div class="text-xs text-text-muted uppercase">主题</div>
              <div class="mt-2 text-lg text-accent-blue">Neo Dark</div>
            </div>
            <div class="sci-panel p-3 col-span-2">
              <div class="text-xs text-text-muted uppercase">状态</div>
              <div class="mt-2 flex items-center gap-2">
                <span class="inline-block h-2.5 w-2.5 bg-accent-green" />
                <span class="text-sm">在线可用</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </NCard>

    <section class="grid gap-4 md:grid-cols-3">
      <NCard
        v-for="item in quickLinks"
        :key="item.to"
        class="sci-panel!"
        embedded
      >
        <div class="space-y-4">
          <h3 class="m-0 text-lg tracking-[0.04em]">{{ item.title }}</h3>
          <p class="m-0 text-sm text-text-muted leading-6">{{ item.desc }}</p>
          <RouterLink :to="item.to" class="inline-flex">
            <AppButton :accent="item.accent" ghost size="small">进入</AppButton>
          </RouterLink>
        </div>
      </NCard>
    </section>
  </section>
</template>
