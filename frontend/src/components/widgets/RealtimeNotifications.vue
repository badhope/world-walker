<template>
  <teleport to="body">
    <transition name="notification-slide">
      <div v-if="notifications.length > 0" class="notification-container">
        <transition-group name="notification-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            :class="['notification-item', `notification-${notification.level}`]"
          >
            <div class="notification-icon">
              <el-icon v-if="notification.level === 'success'"><CircleCheckFilled /></el-icon>
              <el-icon v-else-if="notification.level === 'warning'"><WarningFilled /></el-icon>
              <el-icon v-else-if="notification.level === 'error'"><CircleCloseFilled /></el-icon>
              <el-icon v-else><InfoFilled /></el-icon>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
            </div>
            <el-button
              class="notification-close"
              text
              @click="removeNotification(notification.id)"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </transition-group>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Close, InfoFilled, CircleCheckFilled, WarningFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { useWebSocket } from '@/utils/websocket'

interface Notification {
  id: string
  title: string
  message: string
  level: 'info' | 'success' | 'warning' | 'error'
  duration?: number
}

const notifications = ref<Notification[]>([])
let notificationId = 0

const addNotification = (notification: Omit<Notification, 'id'>) => {
  const id = `notification-${++notificationId}`
  const newNotification: Notification = {
    id,
    ...notification,
    duration: notification.duration ?? 5000
  }
  
  notifications.value.push(newNotification)
  
  // 自动移除
  if (newNotification.duration > 0) {
    setTimeout(() => {
      removeNotification(id)
    }, newNotification.duration)
  }
  
  return id
}

const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const clearAll = () => {
  notifications.value = []
}

// WebSocket 集成
const { state, connect, disconnect, subscribe } = useWebSocket()

onMounted(async () => {
  // 连接到 WebSocket
  try {
    await connect(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/notifications`)
    
    // 订阅通知频道
    subscribe('notifications:*', (message) => {
      if (message.type === 'notification' || message.type === 'success' || message.type === 'warning' || message.type === 'error' || message.type === 'info') {
        addNotification({
          title: message.data.title,
          message: message.data.content,
          level: message.data.level || 'info'
        })
      }
    })
  } catch (error) {
    console.error('WebSocket 连接失败:', error)
  }
})

onUnmounted(() => {
  disconnect()
})

// 导出给外部使用
defineExpose({
  addNotification,
  removeNotification,
  clearAll,
  success: (title: string, message: string) => 
    addNotification({ title, message, level: 'success' }),
  warning: (title: string, message: string) => 
    addNotification({ title, message, level: 'warning' }),
  error: (title: string, message: string) => 
    addNotification({ title, message, level: 'error' }),
  info: (title: string, message: string) => 
    addNotification({ title, message, level: 'info' })
})
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  gap: 12px;
}

.notification-info {
  border-left: 4px solid #409eff;
}

.notification-success {
  border-left: 4px solid #67c23a;
}

.notification-warning {
  border-left: 4px solid #e6a23c;
}

.notification-error {
  border-left: 4px solid #f56c6c;
}

.notification-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.notification-info .notification-icon {
  color: #409eff;
}

.notification-success .notification-icon {
  color: #67c23a;
}

.notification-warning .notification-icon {
  color: #e6a23c;
}

.notification-error .notification-icon {
  color: #f56c6c;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.notification-close {
  flex-shrink: 0;
  padding: 4px;
}

/* 动画 */
.notification-slide-enter-active,
.notification-slide-leave-active {
  transition: all 0.3s ease;
}

.notification-slide-enter-from,
.notification-slide-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-list-enter-active,
.notification-list-leave-active {
  transition: all 0.3s ease;
}

.notification-list-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-list-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-list-move {
  transition: transform 0.3s ease;
}
</style>
