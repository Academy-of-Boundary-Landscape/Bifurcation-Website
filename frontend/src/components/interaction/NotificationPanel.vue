<script setup lang="ts">
import { NCard, NButton } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { ref } from 'vue'
import type { Notification } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'
import { useMutation } from '@tanstack/vue-query'
import { put } from '@/services/http'

// 获取通知列表
const { data: notifications, isLoading, refetch } = useQuery<Notification[]>({
  queryKey: ['notifications', 'panel'],
  queryFn: () => get<Notification[]>('/interaction/notifications'),
})

// 获取未读数量
const { data: unreadCount } = useQuery({
  queryKey: ['unread-count'],
  queryFn: () => get<{ unread_count: number }>('/interaction/notifications/unread-count'),
})

// 标记单个通知为已读
const { mutate: markAsRead } = useMutation({
  mutationFn: (notificationId: number) => put(`/interaction/notifications/${notificationId}/read`),
  onSuccess: (_, notificationId) => {
    // 更新本地缓存
    if (notifications.value) {
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.is_read = true
      }
    }
    refetch()
  }
})

// 标记全部通知为已读
const { mutate: markAllAsRead } = useMutation({
  mutationFn: () => put(`/interaction/notifications/read`),
  onSuccess: () => {
    refetch()
  }
})

function handleRefresh() {
  void refetch()
}

function handleMarkAsRead(notificationId: number) {
  markAsRead(notificationId)
}

function handleMarkAllAsRead() {
  markAllAsRead()
}
</script>

<template>
  <n-card class="bg-#1a1a1a border-#2a2a2a">
    <template #header>
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-bold text-white">通知中心</h2>
        <div class="flex items-center gap-2">
          <span class="text-sm text-#666666">{{ notifications?.length || 0 }} 条通知</span>
          <span v-if="(unreadCount?.unread_count ?? 0) > 0" class="text-sm text-#8b5cf6 bg-#2a2a2a px-2 py-1 rounded-full">
            {{ unreadCount?.unread_count ?? 0 }} 条未读
          </span>
        </div>
      </div>
    </template>
    
    <!-- 加载状态 -->
    <n-card v-if="isLoading" class="bg-#2a2a2a border-#3a3a3a">
      <div class="text-center py-8">
        <div class="animate-spin w-6 h-6 mx-auto mb-2"></div>
        <p class="text-#666666">加载中...</p>
      </div>
    </n-card>
    
    <!-- 空状态 -->
    <n-card v-if="!notifications || notifications.length === 0" class="bg-#2a2a2a border-#3a3a3a">
      <div class="text-center py-12">
        <div class="text-6xl mb-4">🔔</div>
        <h3 class="text-xl font-bold text-white mb-2">暂无通知</h3>
        <p class="text-#666666 mb-8">您还没有收到任何通知</p>
        
        <div class="flex flex-col sm:flex-row gap-4">
          <n-button 
            type="primary" 
            size="large" 
            :component="RouterLink" 
            :to="{ name: 'books' }"
          >
            开始创作
          </n-button>
          
          <n-button 
            type="default" 
            size="large" 
            @click="handleRefresh"
          >
            刷新
          </n-button>
        </div>
      </div>
    </n-card>
    
    <!-- 通知列表 -->
    <div v-else class="space-y-4">
      <n-card 
        v-for="notification in notifications" 
        :key="notification.id" 
        class="bg-#2a2a2a border-#3a3a3a hover:border-#4a4a4a transition-colors cursor-pointer"
            @click="$router.push({ name: 'story-node', params: { nodeId: notification.node_id } })"
      >
        <div class="flex items-start gap-4">
          <!-- 图标 -->
          <div class="flex-shrink-0 mt-1">
            <div v-if="notification.type === 'branched'" class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-xl">
              🌿
            </div>
            <div v-else-if="notification.type === 'liked'" class="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center text-white text-xl">
              👍
            </div>
            <div v-else-if="notification.type === 'commented'" class="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white text-xl">
              💬
            </div>
            <div v-else-if="notification.type === 'approved'" class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xl">
              ✅
            </div>
            <div v-else-if="notification.type === 'rejected'" class="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center text-white text-xl">
              ❌
            </div>
            <div v-else class="w-10 h-10 bg-gray-500 rounded-full flex items-center justify-center text-white text-xl">
              ℹ️
            </div>
          </div>
          
          <!-- 内容 -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white line-clamp-2">
              <span v-if="notification.sender?.username">
                <strong>{{ notification.sender.username }}</strong>
              </span>
              <span v-else>
                <strong>系统</strong>
              </span>
              <span v-if="notification.type === 'branched'">
                创建了新分支
              </span>
              <span v-else-if="notification.type === 'liked'">
                点赞了您的节点
              </span>
              <span v-else-if="notification.type === 'commented'">
                评论了您的节点
              </span>
              <span v-else-if="notification.type === 'approved'">
                审核通过了您的投稿节点
              </span>
              <span v-else-if="notification.type === 'rejected'">
                审核未通过您的投稿节点
              </span>
              <span v-else>
                {{ notification.message }}
              </span>
            </p>
            
            <div class="flex items-center gap-2 mt-2">
              <span class="text-xs text-#666666">
                {{ new Date(notification.created_at).toLocaleString('zh-CN') }}
              </span>
              
              <span v-if="!notification.is_read" class="text-xs text-#8b5cf6 bg-#2a2a2a px-2 py-0.5 rounded-full">
                新
              </span>
            </div>
          </div>
          
          <!-- 标记为已读按钮 -->
          <div v-if="!notification.is_read" class="flex-shrink-0">
            <n-button 
              text 
              size="small" 
              class="text-#8b5cf6 hover:text-white transition-colors"
              @click.stop="handleMarkAsRead(notification.id)"
            >
              标记已读
            </n-button>
          </div>
        </div>
      </n-card>
    </div>
    
    <!-- 查看全部按钮 -->
    <div class="mt-6 flex justify-between items-center">
      <n-button 
        type="primary" 
        size="large" 
        :component="RouterLink" 
            :to="{ name: 'notifications' }"
      >
        查看全部通知
      </n-button>
      
      <n-button 
        type="default" 
        size="large" 
        @click="handleMarkAllAsRead"
      >
        全部标记为已读
      </n-button>
    </div>
  </n-card>
</template>
