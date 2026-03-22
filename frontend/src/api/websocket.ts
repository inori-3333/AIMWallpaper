import type { ChatMessage } from '../types'

type MessageHandler = (msg: ChatMessage) => void
type StatusHandler = (connected: boolean) => void

export class ChatWebSocket {
  private ws: WebSocket | null = null
  private projectId: string
  private onMessage: MessageHandler
  private onStatusChange: StatusHandler
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(projectId: string, onMessage: MessageHandler, onStatusChange: StatusHandler) {
    this.projectId = projectId
    this.onMessage = onMessage
    this.onStatusChange = onStatusChange
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/chat/${this.projectId}`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.onStatusChange(true)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ChatMessage
        this.onMessage(data)
      } catch {
        console.error('Failed to parse WebSocket message')
      }
    }

    this.ws.onclose = () => {
      this.onStatusChange(false)
      this._tryReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  send(message: { type: string; content: string }) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    this.maxReconnectAttempts = 0 // prevent reconnect
    this.ws?.close()
    this.ws = null
  }

  private _tryReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }
}
