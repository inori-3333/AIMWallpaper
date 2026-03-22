import { create } from 'zustand'
import type { ChatMessage } from '../types'

interface ChatState {
  messages: ChatMessage[]
  isConnected: boolean
  isThinking: boolean
  addMessage: (msg: ChatMessage) => void
  setConnected: (connected: boolean) => void
  setThinking: (thinking: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isConnected: false,
  isThinking: false,
  addMessage: (msg) =>
    set((state) => ({
      messages: [...state.messages, msg],
      isThinking: msg.type === 'ai_thinking',
    })),
  setConnected: (connected) => set({ isConnected: connected }),
  setThinking: (thinking) => set({ isThinking: thinking }),
  clearMessages: () => set({ messages: [], isThinking: false }),
}))
