<script setup lang="ts">
import { NCard, NButton, NSpace, NTag, NSpin, NTimeline, NTimelineItem, NAvatar } from 'naive-ui'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, watch } from 'vue'
import type { Notification } from '@/types/models'
import { useQuery, useMutation } from '@tanstack/vue-query'
import { get, put } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

// 获取通知列表
const { data: notifications, isLoading, refetch } = useQuery<Notification[]>({
  queryKey: ['notifications'],
  queryFn: () => get<Notification[]>('/interaction/notifications'),
})

// 获取未读数量
const { data: unreadCount } = useQuery({
  queryKey: ['unread-count'],
  queryFn: () => get<{ unread_count: number }>('/interaction/notifications/unread-count'),
})

// 当前筛选条件
const filterType = ref<string>('all')

// 筛选通知列表
const filteredNotifications = computed(() => {
  if (!notifications.value) return []
  
  if (filterType.value === 'all') return notifications.value
  
  return notifications.value.filter(notification => notification.type === filterType.value)
})

// 标记单个通知为已读
const { mutate: markAsRead, isPending: marking } = useMutation({
  mutationFn: (notificationId: number) => put<{ detail: string }>('/interaction/notifications/' + notificationId + '/read'),
  onSuccess: (_, notificationId) => {
    message.success('通知状态已更新')
    // 更新缓存
    if (notifications.value) {
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.is_read = true
      }
    }
    refetch()
  },
  onError: (error) => {
    console.error('标记失败:', error)
    message.error('标记失败，请重试')
  }
})

// 标记全部为已读
const { mutate: markAllAsRead, isPending: markingAll } = useMutation({
  mutationFn: () => put<{ detail: string }>('/interaction/notifications/read'),
  onSuccess: () => {
    message.success('所有通知已标记为已读')
    // 更新缓存
    if (notifications.value) {
      notifications.value.forEach(notification => {
        notification.is_read = true
      })
    }
    refetch()
  },
  onError: (error) => {
    console.error('标记全部失败:', error)
    message.error('标记失败，请重试')
  }
})

// 切换筛选条件
function setFilter(type: string) {
  filterType.value = type
}

function handleMarkAsRead(notificationId: number) {
  markAsRead(notificationId)
}

function handleMarkAllAsRead() {
  markAllAsRead()
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-white mb-2">通知中心</h1>
    <p class="text-#666666 mb-8">查看您的最新动态</p>
    
    <!-- 筛选器 -->
    <n-card class="bg-#1a1a1a border-#2a2a2a mb-6">
      <template #header>
        <h2 class="text-xl font-bold text-white">筛选器</h2>
      </template>
      
      <div class="flex flex-wrap gap-3">
        <n-tag 
          :type="filterType === 'all' ? 'primary' : 'default'"
          size="small" 
          @click="setFilter('all')"
        >
          全部
        </n-tag>
        <n-tag 
          :type="filterType === 'branched' ? 'success' : 'default'"
          size="small" 
          @click="setFilter('branched')"
        >
          新分支
        </n-tag>
        <n-tag 
          :type="filterType === 'liked' ? 'warning' : 'default'"
          size="small" 
          @click="setFilter('liked')"
        >
          点赞
        </n-tag>
        <n-tag 
          :type="filterType === 'commented' ? 'info' : 'default'"
          size="small" 
          @click="setFilter('commented')"
        >
          评论
        </n-tag>
        <n-tag 
          :type="filterType === 'approved' ? 'success' : 'default'"
          size="small" 
          @click="setFilter('approved')"
        >
          审核通过
        </n-tag>
        <n-tag 
          :type="filterType === 'rejected' ? 'error' : 'default'"
          size="small" 
          @click="setFilter('rejected')"
        >
          审核拒绝
        </n-tag>
      </div>
    </n-card>
    
    <!-- 通知列表 -->
    <n-spin :show="isLoading">
      <div v-if="!filteredNotifications || filteredNotifications.length === 0" class="text-center py-12">
        <div class="text-6xl mb-4">🔔</div>
        <h3 class="text-xl font-bold text-white mb-2">暂无通知</h3>
        <p class="text-#666666">您还没有收到任何通知</p>
        
        <div class="mt-6">
          <n-button 
            type="primary" 
            size="large" 
            :component="RouterLink" 
            :to="{ name: 'books' }"
          >
            开始创作
          </n-button>
        </div>
      </div>
      
      <div v-else class="space-y-4">
        <n-card 
          v-for="notification in filteredNotifications" 
          :key="notification.id" 
          class="bg-#1a1a1a border-#2a2a2a hover:border-#8b5cf6 transition-colors"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div v-if="notification.type === 'branched'" class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white">
                  🌿
                </div>
                <div v-else-if="notification.type === 'liked'" class="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center text-white">
                  👍
                </div>
                <div v-else-if="notification.type === 'commented'" class="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white">
                  💬
                </div>
                <div v-else-if="notification.type === 'approved'" class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center text-white">
                  ✅
                </div>
                <div v-else-if="notification.type === 'rejected'" class="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center text-white">
                  ❌
                </div>
                <div v-else class="w-10 h-10 bg-gray-500 rounded-full flex items-center justify-center text-white">
                  ℹ️
                </div>
                
                <div>
                  <h3 class="text-lg font-semibold text-white">{{ notification.sender?.username }}</h3>
                  <p class="text-#666666 text-sm">
                    {{ new Date(notification.created_at).toLocaleString('zh-CN') }}
                  </p>
                </div>
              </div>
              
              <div v-if="!notification.is_read" class="flex items-center gap-2">
                <n-tag type="warning" size="small">新</n-tag>
                <n-button 
                  size="small" 
                  type="primary" 
                  @click="handleMarkAsRead(notification.id)"
                  :loading="marking && notifications?.find(n => n.id === notification.id)?.id === notification.id"
                  :disabled="marking && notifications?.find(n => n.id === notification.id)?.id === notification.id"
                >
                  标记已读
                </n-button>
              </div>
            </div>
          </template>
          
          <!-- 通知内容 -->
          <div class="prose prose-invert max-w-none text-#d9d9d9 leading-relaxed whitespace-pre-wrap">
            <p v-if="notification.type === 'branched'">
              <strong>{{ notification.sender?.username }}</strong> 从您的节点创建了新分支
            </p>
            <p v-else-if="notification.type === 'liked'">
              <strong>{{ notification.sender?.username }}</strong> 点赞了您的节点
            </p>
            <p v-else-if="notification.type === 'commented'">
              <strong>{{ notification.sender?.username }}</strong> 评论了您的节点
            </p>
            <p v-else-if="notification.type === 'approved'">
              恭喜！您的投稿节点已被审核通过
            </p>
            <p v-else-if="notification.type === 'rejected'">
              很抱歉，您的投稿节点未通过审核
            </p>
            <p v-else>
              {{ notification.message || '未知类型的通知' }}
            </p>
          </div>
          
          <!-- 节点链接 -->
          <div v-if="notification.node_id" class="mt-6">
            <n-button 
              type="primary" 
              :component="RouterLink" 
              :to="{ name: 'story-node', params: { nodeId: notification.node_id } }"
            >
              查看节点
            </n-button>
          </div>
        </n-card>
      </div>
    </n-spin>
    
    <!-- 底部操作 -->
    <div class="mt-8 flex justify-end">
      <n-button 
        type="primary" 
        @click="handleMarkAllAsRead"
        :loading="markingAll"
        :disabled="markingAll"
      >
        全部标记为已读
      </n-button>
    </div>
  </div>
</template>
