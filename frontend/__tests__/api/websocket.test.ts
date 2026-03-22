import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ChatWebSocket } from '../../src/api/websocket'

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1
  readyState = MockWebSocket.OPEN
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  sent: string[] = []

  send(data: string) { this.sent.push(data) }
  close() { this.onclose?.() }
}

describe('ChatWebSocket', () => {
  let mockWs: MockWebSocket

  beforeEach(() => {
    mockWs = new MockWebSocket()
    // Use a class wrapper so `new WebSocket(url)` works as a constructor
    const FakeWebSocket = function () { return mockWs } as unknown as typeof WebSocket
    FakeWebSocket.OPEN = 1 as typeof WebSocket.OPEN
    FakeWebSocket.CLOSED = 3 as typeof WebSocket.CLOSED
    FakeWebSocket.CLOSING = 2 as typeof WebSocket.CLOSING
    FakeWebSocket.CONNECTING = 0 as typeof WebSocket.CONNECTING
    vi.stubGlobal('WebSocket', FakeWebSocket)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('connects and reports status', () => {
    const onMessage = vi.fn()
    const onStatus = vi.fn()
    const ws = new ChatWebSocket('1', onMessage, onStatus)
    ws.connect()
    mockWs.onopen?.()
    expect(onStatus).toHaveBeenCalledWith(true)
  })

  it('sends messages', () => {
    const ws = new ChatWebSocket('1', vi.fn(), vi.fn())
    ws.connect()
    mockWs.onopen?.()
    ws.send({ type: 'user_message', content: 'Hello' })
    expect(mockWs.sent).toHaveLength(1)
    expect(JSON.parse(mockWs.sent[0])).toEqual({ type: 'user_message', content: 'Hello' })
  })

  it('handles incoming messages', () => {
    const onMessage = vi.fn()
    const ws = new ChatWebSocket('1', onMessage, vi.fn())
    ws.connect()
    mockWs.onmessage?.({ data: JSON.stringify({ type: 'ai_message', content: 'Hi!' }) })
    expect(onMessage).toHaveBeenCalledWith({ type: 'ai_message', content: 'Hi!' })
  })

  it('reports disconnection', () => {
    const onStatus = vi.fn()
    const ws = new ChatWebSocket('1', vi.fn(), onStatus)
    ws.connect()
    ws.disconnect()
    expect(onStatus).toHaveBeenCalledWith(false)
  })
})
