import { useEffect, useRef, useCallback } from 'react'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { ChatWebSocket } from '../../api/websocket'
import { useChatStore } from '../../stores/chatStore'
import { useProjectStore } from '../../stores/projectStore'
import type { ChatMessage } from '../../types'

export function ChatPanel() {
  const wsRef = useRef<ChatWebSocket | null>(null)
  const { messages, isConnected, isThinking, addMessage, setConnected } = useChatStore()
  const projectId = useProjectStore((s) => s.currentProjectId)

  const handleMessage = useCallback((msg: ChatMessage) => {
    addMessage(msg)
  }, [addMessage])

  const handleStatus = useCallback((connected: boolean) => {
    setConnected(connected)
  }, [setConnected])

  useEffect(() => {
    if (!projectId) return

    const ws = new ChatWebSocket(projectId, handleMessage, handleStatus)
    ws.connect()
    wsRef.current = ws

    return () => {
      ws.disconnect()
      wsRef.current = null
    }
  }, [projectId, handleMessage, handleStatus])

  const handleSend = (content: string) => {
    addMessage({ type: 'user_message', content })
    wsRef.current?.send({ type: 'user_message', content })
  }

  if (!projectId) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 text-sm">
        Select or create a project to start chatting
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 border-b border-gray-700 flex items-center justify-between">
        <span className="text-sm font-medium">AI Chat</span>
        <span className={`text-xs ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      <MessageList messages={messages} isThinking={isThinking} />
      <ChatInput onSend={handleSend} disabled={!isConnected} />
    </div>
  )
}
