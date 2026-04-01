<script setup lang="ts">
import { NCard, NButton } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { ref } from 'vue'
import type { User } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'

// 获取用户列表
const { data: users, isLoading, refetch } = useQuery<User[]>({
  queryKey: ['users'],
  queryFn: () => get<User[]>('/auth/users'),
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-white mb-2">用户管理</h1>
    <p class="text-#666666 mb-8">查看和管理所有用户账户</p>
    
    <!-- 筛选器 -->
    <n-card class="bg-#1a1a1a border-#2a2a2a mb-6">
      <template #header>
        <h2 class="text-xl font-bold text-white">筛选器</h2>
      </template>
      
      <div class="flex flex-wrap gap-3">
        <n-tag size="small" type="primary">全部</n-tag>
        <n-tag size="small" type="success">管理员</n-tag>
        <n-tag size="small" type="warning">作者</n-tag>
        <n-tag size="small" type="error">已封禁</n-tag>
      </div>
    </n-card>
    
    <!-- 用户列表 -->
    <n-spin :show="isLoading">
      <div v-if="!users || users.length === 0" class="text-center py-12">
        <div class="text-6xl mb-4">👥</div>
        <h3 class="text-xl font-bold text-white mb-2">暂无用户</h3>
        <p class="text-#666666">当前没有创建任何用户账户</p>
      </div>
      
      <div v-else class="space-y-4">
        <n-card 
          v-for="user in users" 
          :key="user.id" 
          class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        >
          <div class="flex items-center gap-4">
            <n-avatar 
              :size="40" 
              :src="user.avatar"
              class="cursor-pointer"
              @click="$router.push({ name: 'profile', params: { userId: user.id } })"
            >
              {{ user.username?.charAt(0).toUpperCase() }}
            </n-avatar>
            
            <div class="flex-1 min-w-0">
              <h3 class="text-lg font-semibold text-white">{{ user.username }}</h3>
              <p class="text-#666666 text-sm">
                <span v-if="user.role === 'admin'">管理员</span>
                <span v-else-if="user.role === 'writer'">作者</span>
                <span v-else-if="user.role === 'banned'">已封禁</span>
                <span v-else>{{ user.role }}</span>
                · {{ user.email }} · {{ new Date(user.created_at).toLocaleDateString('zh-CN') }}
              </p>
              
              <div class="flex items-center gap-2 mt-2">
                <span class="text-xs text-#666666">
                  投稿数: {{ user.nodes_count || 0 }}
                </span>
                <span class="text-xs text-#666666">
                  点赞数: {{ user.likes_count || 0 }}
                </span>
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <n-button 
                size="small" 
                type="primary" 
                :component="RouterLink" 
                :to="{ name: 'profile', params: { userId: user.id } }"
              >
                查看资料
              </n-button>
              
              <n-button 
                size="small" 
                type="default" 
                @click="refetch"
              >
                刷新
              </n-button>
            </div>
          </div>
        </n-card>
      </div>
    </n-spin>
  </div>
</template>