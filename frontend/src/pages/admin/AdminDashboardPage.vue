<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { ref } from 'vue'
import type { StoryNodeTreeItem } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'

// 获取待审核节点数量
const { data: pendingCount, isLoading: pendingLoading } = useQuery({
  queryKey: ['pending-count'],
  queryFn: () => get<{ count: number }>('/admin/nodes/pending/count'),
})

// 获取今日新增节点数量
const { data: todayCount, isLoading: todayLoading } = useQuery({
  queryKey: ['today-count'],
  queryFn: () => get<{ count: number }>('/admin/nodes/today/count'),
})

// 获取总节点数
const { data: totalCount, isLoading: totalLoading } = useQuery({
  queryKey: ['total-count'],
  queryFn: () => get<{ count: number }>('/story/node/count'),
})

// 获取用户总数
const { data: userCount, isLoading: userLoading } = useQuery({
  queryKey: ['user-count'],
  queryFn: () => get<{ count: number }>('/auth/users/count'),
})

// 获取评论总数
const { data: commentCount, isLoading: commentLoading } = useQuery({
  queryKey: ['comment-count'],
  queryFn: () => get<{ count: number }>('/interaction/comment/count'),
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-white mb-2">管理员仪表盘</h1>
    <p class="text-#666666 mb-8">查看平台运营数据和管理入口</p>
    
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <n-card 
        class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        :bordered="true"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-#666666 text-sm">待审核节点</p>
            <h2 class="text-3xl font-bold text-white mt-1">{{ pendingCount?.count || 0 }}</h2>
          </div>
          <div class="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center text-white">
            📋
          </div>
        </div>
        <div class="mt-4">
          <n-button 
            type="primary" 
            size="small" 
            :component="RouterLink" 
            to="{ name: 'admin-pending' }"
          >
            查看列表
          </n-button>
        </div>
      </n-card>
      
      <n-card 
        class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        :bordered="true"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-#666666 text-sm">今日新增</p>
            <h2 class="text-3xl font-bold text-white mt-1">{{ todayCount?.count || 0 }}</h2>
          </div>
          <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white">
            📅
          </div>
        </div>
        <div class="mt-4">
          <n-button 
            type="primary" 
            size="small" 
            :component="RouterLink" 
            to="{ name: 'books' }"
          >
            查看详情
          </n-button>
        </div>
      </n-card>
      
      <n-card 
        class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        :bordered="true"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-#666666 text-sm">总节点数</p>
            <h2 class="text-3xl font-bold text-white mt-1">{{ totalCount?.count || 0 }}</h2>
          </div>
          <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white">
            🌳
          </div>
        </div>
        <div class="mt-4">
          <n-button 
            type="primary" 
            size="small" 
            :component="RouterLink" 
            to="{ name: 'admin-books' }"
          >
            管理故事册
          </n-button>
        </div>
      </n-card>
      
      <n-card 
        class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        :bordered="true"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-#666666 text-sm">活跃用户</p>
            <h2 class="text-3xl font-bold text-white mt-1">{{ userCount?.count || 0 }}</h2>
          </div>
          <div class="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center text-white">
            👥
          </div>
        </div>
        <div class="mt-4">
          <n-button 
            type="primary" 
            size="small" 
            :component="RouterLink" 
            to="{ name: 'admin-users' }"
          >
            用户管理
          </n-button>
        </div>
      </n-card>
    </div>
    
    <!-- 快速访问 -->
    <n-card class="bg-#1a1a1a border-#2a2a2a">
      <template #header>
        <h2 class="text-xl font-bold text-white">快速访问</h2>
      </template>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <n-card 
          class="bg-#2a2a2a border-#3a3a3a hover:bg-#3a3a3a transition-colors cursor-pointer"
          @click="$router.push({ name: 'admin-pending' })"
        >
          <div class="text-center p-6">
            <div class="text-3xl mb-2">📋</div>
            <h3 class="text-lg font-semibold text-white mb-2">待审核节点</h3>
            <p class="text-#666666 text-sm">查看并处理待审核的创作内容</p>
          </div>
        </n-card>
        
        <n-card 
          class="bg-#2a2a2a border-#3a3a3a hover:bg-#3a3a3a transition-colors cursor-pointer"
          @click="$router.push({ name: 'admin-books' })"
        >
          <div class="text-center p-6">
            <div class="text-3xl mb-2">📚</div>
            <h3 class="text-lg font-semibold text-white mb-2">故事册管理</h3>
            <p class="text-#666666 text-sm">管理故事册状态和阶段</p>
          </div>
        </n-card>
        
        <n-card 
          class="bg-#2a2a2a border-#3a3a3a hover:bg-#3a3a3a transition-colors cursor-pointer"
          @click="$router.push({ name: 'admin-users' })"
        >
          <div class="text-center p-6">
            <div class="text-3xl mb-2">👥</div>
            <h3 class="text-lg font-semibold text-white mb-2">用户管理</h3>
            <p class="text-#666666 text-sm">查看和管理用户账户</p>
          </div>
        </n-card>
      </div>
    </n-card>
    
    <!-- 最近活动 -->
    <n-card class="bg-#1a1a1a border-#2a2a2a mt-8">
      <template #header>
        <h2 class="text-xl font-bold text-white">最近活动</h2>
      </template>
      
      <div class="space-y-4">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white">
            📝
          </div>
          <div>
            <p class="text-#d9d9d9">用户 "张三" 提交了新节点</p>
            <p class="text-#666666 text-sm">2分钟前 · 待审核</p>
          </div>
        </div>
        
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white">
            ✅
          </div>
          <div>
            <p class="text-#d9d9d9">节点 #1234 已通过审核</p>
            <p class="text-#666666 text-sm">5分钟前 · 发布成功</p>
          </div>
        </div>
        
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white">
            ❌
          </div>
          <div>
            <p class="text-#d9d9d9">节点 #5678 审核未通过</p>
            <p class="text-#666666 text-sm">10分钟前 · 需要修改</p>
          </div>
        </div>
      </div>
    </n-card>
  </div>
</template>