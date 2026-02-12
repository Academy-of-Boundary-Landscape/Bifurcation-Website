import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Notification } from '@/types'

export const useNotificationStore = defineStore('notification', () => {
  // State
  const notifications = ref<Notification[]>([])
  const unreadCount = ref<number>(0)

  // Getters
  const hasUnread = computed(() => unreadCount.value > 0)

  // Actions
  const setNotifications = (list: Notification[]) => {
    notifications.value = list
    unreadCount.value = list.filter((n) => !n.is_read).length
  }

  const addNotification = (notification: Notification) => {
    notifications.value.unshift(notification)
    if (!notification.is_read) {
      unreadCount.value++
    }
  }

  const markAsRead = (id: number) => {
    const notification = notifications.value.find((n) => n.id === id)
    if (notification && !notification.is_read) {
      notification.is_read = true
      unreadCount.value--
    }
  }

  const markAllAsRead = () => {
    notifications.value.forEach((n) => {
      n.is_read = true
    })
    unreadCount.value = 0
  }

  const clearNotifications = () => {
    notifications.value = []
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    hasUnread,
    setNotifications,
    addNotification,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  }
})