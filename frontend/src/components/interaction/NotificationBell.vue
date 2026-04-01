<script setup lang="ts">
import { NBadge, NButton } from 'naive-ui'
import { RouterLink } from 'vue-router'
import { ref, computed } from 'vue'
import type { Notification } from '@/types/models'
import { useQuery } from '@tanstack/vue-query'
import { get } from '@/services/http'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 获取未读通知数量
const { data: unreadCount } = useQuery({
  queryKey: ['unread-count'],
  queryFn: () => get<{ unread_count: number }>('/interaction/notifications/unread-count'),
})

// 显示面板
const showPanel = ref(false)

// 获取通知列表（前5条）
const { data: notificationData, isLoading } = useQuery({
  queryKey: ['notifications', 'bell'],
  queryFn: () => get<Notification[]>('/interaction/notifications?limit=5'),
})
</script>

<template>
  <div class="relative">
    <!-- 通知铃铛 -->
    <n-badge 
      v-if="unreadCount?.unread_count > 0" 
      :value="unreadCount?.unread_count" 
      :max="99"
      class="cursor-pointer"
      @click="showPanel = !showPanel"
    >
      <n-button 
        text 
        size="large" 
        class="text-white hover:text-#8b5cf6 transition-colors"
      >
        🔔
      </n-button>
    </n-badge>
    
    <!-- 默认铃铛（无未读） -->
    <n-button 
      v-else 
      text 
      size="large" 
      class="text-white hover:text-#8b5cf6 transition-colors cursor-pointer"
      @click="showPanel = !showPanel"
    >
      🔔
    </n-button>
    
    <!-- 下拉面板 -->
    <div 
      v-if="showPanel" 
      class="absolute right-0 mt-2 w-80 bg-#1a1a1a border border-#2a2a2a rounded-lg shadow-xl z-50"
      @click.stop
    >
      <div class="p-4 border-b border-#2a2a2a">
        <h3 class="font-bold text-white">通知中心</h3>
      </div>
      
      <!-- 通知列表 -->
      <div class="max-h-96 overflow-y-auto">
        <div v-if="!notificationData || notificationData.length === 0" class="p-4 text-center text-#666666">
          <p>暂无通知</p>
        </div>
        
        <div v-else class="space-y-3 p-2">
          <div 
            v-for="notification in notificationData" 
            :key="notification.id" 
            class="flex items-start gap-3 p-3 hover:bg-#2a2a2a transition-colors rounded cursor-pointer"
            @click="$router.push({ name: 'story-node', params: { nodeId: notification.node_id } })"
          >
            <!-- 图标 -->
            <div class="flex-shrink-0 mt-1">
              <div v-if="notification.type === 'branched'" class="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs">
                🌿
              </div>
              <div v-else-if="notification.type === 'liked'" class="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center text-white text-xs">
                👍
              </div>
              <div v-else-if="notification.type === 'commented'" class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
                💬
              </div>
              <div v-else-if="notification.type === 'approved'" class="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs">
                ✅
              </div>
              <div v-else-if="notification.type === 'rejected'" class="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white text-xs">
                ❌
              </div>
              <div v-else class="w-6 h-6 bg-gray-500 rounded-full flex items-center justify-center text-white text-xs">
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
              <p class="text-xs text-#666666">
                {{ new Date(notification.created_at).toLocaleString('zh-CN') }}
              </p>
            </div>
            
            <!-- 阅读状态 -->
            <div v-if="!notification.is_read" class="flex-shrink-0 mt-1">
              <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 查看全部按钮 -->
      <div class="p-4 border-t border-#2a2a2a">
        <n-button 
          size="small" 
          type="primary" 
          :component="RouterLink" 
          to="{ name: 'notifications' }"
        >
          查看全部通知
        </n-button>
      </div>
    </div>
  </div>
</template>
