import { ref, computed } from 'vue'

export interface WebSocketMessage {
  type: string
  channel: string
  data: unknown
  timestamp: string
  sender?: string
  target?: string
}

export interface ConnectionState {
  connected: boolean
  connectionId: string | null
  userId: string | null
  subscriptions: string[]
  lastError: string | null
}

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private heartbeatInterval: number | null = null
  private messageHandlers: Map<string, Set<(message: WebSocketMessage) => void>> = new Map()
  private connectionState = ref<ConnectionState>({
    connected: false,
    connectionId: null,
    userId: null,
    subscriptions: [],
    lastError: null
  })

  constructor() {
    this.connectionState = ref({
      connected: false,
      connectionId: null,
      userId: null,
      subscriptions: [],
      lastError: null
    })
  }

  get state() {
    return this.connectionState
  }

  get isConnected() {
    return computed(() => this.connectionState.value.connected)
  }

  async connect(url: string, userId?: string): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket 已经连接')
      return
    }

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = new URL(url, window.location.origin)
        wsUrl.protocol = wsUrl.protocol.replace('http', 'ws')

        if (userId) {
          wsUrl.searchParams.set('user_id', userId)
        }

        this.ws = new WebSocket(wsUrl.toString())

        this.ws.onopen = () => {
          console.log('WebSocket 连接已建立')
          this.connectionState.value.connected = true
          this.connectionState.value.lastError = null
          this.reconnectAttempts = 0

          this.startHeartbeat()

          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('消息解析失败:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket 错误:', error)
          this.connectionState.value.lastError = '连接错误'
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket 连接已关闭')
          this.connectionState.value.connected = false
          this.stopHeartbeat()

          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
            setTimeout(() => {
              this.connect(url, userId)
            }, this.reconnectDelay)
          }
        }
      } catch (error) {
        console.error('WebSocket 连接失败:', error)
        this.connectionState.value.lastError = '连接失败'
        reject(error)
      }
    })
  }

  disconnect() {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connectionState.value = {
      connected: false,
      connectionId: null,
      userId: null,
      subscriptions: [],
      lastError: null
    }
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('收到消息:', message)

    if (message.type === 'ping') {
      this.send({ type: 'ping', channel: 'system', data: {} })
      return
    }

    if (message.type === 'subscription') {
      const subscriptions = this.connectionState.value.subscriptions
      if (!subscriptions.includes(message.channel)) {
        subscriptions.push(message.channel)
      }
    }

    if (message.type === 'unsubscription') {
      const subscriptions = this.connectionState.value.subscriptions
      const index = subscriptions.indexOf(message.channel)
      if (index > -1) {
        subscriptions.splice(index, 1)
      }
    }

    if (message.type === 'error') {
      console.error('WebSocket 错误消息:', message.data)
      this.connectionState.value.lastError = (message.data as Record<string, string>).error
    }

    const handlers = this.messageHandlers.get(message.channel)
    if (handlers) {
      handlers.forEach(handler => handler(message))
    }

    const globalHandlers = this.messageHandlers.get('*')
    if (globalHandlers) {
      globalHandlers.forEach(handler => handler(message))
    }
  }

  send(message: { type: string; channel?: string; data?: unknown; target?: string }) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket 未连接，无法发送消息')
      return
    }

    const messageData = {
      type: message.type,
      channel: message.channel || 'system',
      data: message.data || {},
      target: message.target
    }

    this.ws.send(JSON.stringify(messageData))
  }

  subscribe(channel: string, filters?: Record<string, unknown>) {
    this.send({
      type: 'subscribe',
      channel,
      data: { filters }
    })
  }

  unsubscribe(channel: string) {
    this.send({
      type: 'unsubscribe',
      channel
    })
  }

  broadcast(channel: string, data: unknown) {
    this.send({
      type: 'broadcast',
      channel,
      data
    })
  }

  on(channel: string, handler: (message: WebSocketMessage) => void) {
    if (!this.messageHandlers.has(channel)) {
      this.messageHandlers.set(channel, new Set())
    }
    this.messageHandlers.get(channel)!.add(handler)
  }

  off(channel: string, handler: (message: WebSocketMessage) => void) {
    const handlers = this.messageHandlers.get(channel)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  private startHeartbeat() {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', channel: 'system', data: {} })
      }
    }, 30000)
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

export const wsService = new WebSocketService()

export function useWebSocket() {
  const subscribe = (channel: string, handler: (message: WebSocketMessage) => void) => {
    wsService.on(channel, handler)
    return () => wsService.off(channel, handler)
  }

  return {
    state: wsService.state,
    isConnected: wsService.isConnected,
    connect: (url: string, userId?: string) => wsService.connect(url, userId),
    disconnect: () => wsService.disconnect(),
    subscribe,
    unsubscribe: (channel: string) => wsService.unsubscribe(channel),
    broadcast: (channel: string, data: unknown) => wsService.broadcast(channel, data),
    send: (message: { type: string; channel?: string; data?: unknown; target?: string }) => wsService.send(message)
  }
}