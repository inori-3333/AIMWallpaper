import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../../src/stores/chatStore'

describe('chatStore', () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages()
  })

  it('starts empty', () => {
    const state = useChatStore.getState()
    expect(state.messages).toEqual([])
    expect(state.isConnected).toBe(false)
    expect(state.isThinking).toBe(false)
  })

  it('adds messages', () => {
    useChatStore.getState().addMessage({ type: 'user_message', content: 'Hello' })
    expect(useChatStore.getState().messages).toHaveLength(1)
  })

  it('sets thinking on ai_thinking message', () => {
    useChatStore.getState().addMessage({ type: 'ai_thinking', content: 'Processing...' })
    expect(useChatStore.getState().isThinking).toBe(true)
  })

  it('clears thinking on ai_message', () => {
    useChatStore.getState().addMessage({ type: 'ai_thinking', content: '...' })
    useChatStore.getState().addMessage({ type: 'ai_message', content: 'Done' })
    expect(useChatStore.getState().isThinking).toBe(false)
  })

  it('clears all messages', () => {
    useChatStore.getState().addMessage({ type: 'user_message', content: 'test' })
    useChatStore.getState().clearMessages()
    expect(useChatStore.getState().messages).toEqual([])
  })
})
