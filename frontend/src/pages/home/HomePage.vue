<script setup lang="ts">
import { NButton, NSpace, NCard, NGrid, NGridItem } from 'naive-ui'
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen">
    <!-- Hero 区块 -->
    <section class="py-20 text-center">
      <h1 class="text-4xl md:text-6xl font-bold mb-4 text-white">
        分岔视界
      </h1>
      <p class="text-xl md:text-2xl text-#a0a0a0 mb-8">
        Bifurcation Horizon
      </p>
      <p class="text-lg text-#666666 mb-12 max-w-2xl mx-auto">
        沿着秘封组的故事继续前进，或亲手开启新的世界线。
      </p>
      <n-space justify="center">
        <n-button :component="RouterLink" to="/books" type="primary" size="large">
          开始阅读
        </n-button>
        <n-button :component="RouterLink" to="/register" variant="outline" size="large">
          我要创作
        </n-button>
      </n-space>
    </section>

    <!-- 活动简介 -->
    <section class="py-12">
      <n-card class="bg-#1a1a1a border-#2a2a2a">
        <h2 class="text-2xl font-bold mb-6 text-white">什么是分岔视界？</h2>
        <n-grid :cols="3" :x-gap="16" class="text-#a0a0a0">
          <n-grid-item>
            <div class="text-4xl mb-4">🌳</div>
            <h3 class="text-lg font-semibold mb-2 text-white">树状叙事</h3>
            <p>每个故事都有多个分支，每条分支都可能导向不同的结局。</p>
          </n-grid-item>
          <n-grid-item>
            <div class="text-4xl mb-4">✍️</div>
            <h3 class="text-lg font-semibold mb-2 text-white">共同创作</h3>
            <p>在已有节点上续写，或从任意节点开启新的世界线。</p>
          </n-grid-item>
          <n-grid-item>
            <div class="text-4xl mb-4">🔍</div>
            <h3 class="text-lg font-semibold mb-2 text-white">审核发布</h3>
            <p>所有内容经过审核后发布，保证故事质量。</p>
          </n-grid-item>
        </n-grid>
      </n-card>
    </section>

    <!-- 参与流程 -->
    <section class="py-12">
      <h2 class="text-2xl font-bold mb-8 text-white text-center">如何参与</h2>
      <n-grid :cols="4" :x-gap="16">
        <n-grid-item v-for="step in [
          { icon: '📝', title: '注册登录', desc: '创建账号，开启创作之旅' },
          { icon: '📖', title: '阅读前文', desc: '浏览故事树，了解已有剧情' },
          { icon: '✒️', title: '续写创作', desc: '在节点上续写或开启新分支' },
          { icon: '✅', title: '等待发布', desc: '审核通过后，你的故事将被发布' },
        ]" :key="step.title">
          <n-card class="bg-#1a1a1a border-#2a2a2a text-center">
            <div class="text-4xl mb-4">{{ step.icon }}</div>
            <h3 class="text-lg font-semibold mb-2 text-white">{{ step.title }}</h3>
            <p class="text-#666666">{{ step.desc }}</p>
          </n-card>
        </n-grid-item>
      </n-grid>
    </section>

    <!-- 故事册入口 -->
    <section class="py-12 text-center">
      <h2 class="text-2xl font-bold mb-8 text-white">探索故事</h2>
      <n-button :component="RouterLink" to="/books" type="primary" size="large">
        查看所有故事册
      </n-button>
    </section>
  </div>
</template>