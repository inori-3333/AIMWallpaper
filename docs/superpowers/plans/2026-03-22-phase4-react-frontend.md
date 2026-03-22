# Phase 4: React Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React frontend with three-panel layout (assets, preview, chat), connecting to the FastAPI backend via REST and WebSocket APIs.

**Architecture:** Vite + React 18 + TypeScript app with TailwindCSS for styling and Zustand for state management. Three main panels: AssetPanel (left — upload/manage assets + layer tree), PreviewPanel (center — wallpaper preview), ChatPanel (right — AI conversation). React Query handles REST API caching. WebSocket connection for real-time chat.

**Tech Stack:** React 18, TypeScript, Vite, TailwindCSS, Zustand, TanStack React Query, WebSocket API

**Spec:** `docs/superpowers/specs/2026-03-22-aimwallpaper-design.md` (Sections 6, 7.1)

**Depends on:** Phase 3 (complete backend with REST + WebSocket APIs)

---

## File Structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── src/
│   ├── main.tsx                      ← Create: React entry point
│   ├── App.tsx                       ← Create: three-panel layout
│   ├── api/
│   │   ├── client.ts                 ← Create: axios/fetch REST client
│   │   ├── hooks.ts                  ← Create: React Query hooks for REST APIs
│   │   └── websocket.ts             ← Create: WebSocket connection manager
│   ├── stores/
│   │   ├── projectStore.ts           ← Create: Zustand store for project state
│   │   └── chatStore.ts             ← Create: Zustand store for chat state
│   ├── components/
│   │   ├── Layout/
│   │   │   └── ThreePanel.tsx        ← Create: responsive three-panel layout
│   │   ├── AssetPanel/
│   │   │   ├── AssetPanel.tsx        ← Create: asset management panel
│   │   │   ├── AssetUpload.tsx       ← Create: drag-and-drop file upload
│   │   │   └── LayerTree.tsx         ← Create: layer/effect structure tree
│   │   ├── PreviewPanel/
│   │   │   └── PreviewPanel.tsx      ← Create: wallpaper preview display
│   │   ├── ChatPanel/
│   │   │   ├── ChatPanel.tsx         ← Create: main chat panel
│   │   │   ├── MessageList.tsx       ← Create: chat message display
│   │   │   └── ChatInput.tsx         ← Create: message input with send
│   │   ├── TopNav/
│   │   │   └── TopNav.tsx            ← Create: top navigation bar
│   │   └── common/
│   │       └── Spinner.tsx           ← Create: loading spinner
│   └── types/
│       └── index.ts                  ← Create: shared TypeScript types
├── __tests__/
│   ├── setup.ts                      ← Create: Vitest setup
│   ├── api/
│   │   ├── client.test.ts            ← Create: REST client tests
│   │   └── websocket.test.ts         ← Create: WebSocket tests
│   ├── stores/
│   │   ├── projectStore.test.ts      ← Create: project store tests
│   │   └── chatStore.test.ts         ← Create: chat store tests
│   └── components/
│       ├── ChatPanel.test.tsx         ← Create: ChatPanel component test
│       ├── AssetPanel.test.tsx        ← Create: AssetPanel component test
│       └── PreviewPanel.test.tsx      ← Create: PreviewPanel component test
└── .gitignore
```

---

## Task 1: Project Scaffold (Vite + React + TypeScript + TailwindCSS)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/.gitignore`

- [ ] **Step 1: Scaffold Vite project**

```bash
cd E:\Inori_Code\Intrest\MyIdea\AIMWallpaper
npm create vite@latest frontend -- --template react-ts
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite
npm install zustand @tanstack/react-query
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @testing-library/user-event
```

- [ ] **Step 3: Configure TailwindCSS**

Replace `frontend/src/index.css`:
```css
@import "tailwindcss";
```

Add Tailwind plugin to `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './__tests__/setup.ts',
  },
})
```

- [ ] **Step 4: Create test setup**

```typescript
// frontend/__tests__/setup.ts
import '@testing-library/jest-dom'
```

- [ ] **Step 5: Create minimal App.tsx**

```tsx
// frontend/src/App.tsx
function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <header className="h-12 bg-gray-800 flex items-center px-4 border-b border-gray-700">
        <h1 className="text-lg font-semibold">AIMWallpaper</h1>
      </header>
      <main className="flex-1 flex">
        <div className="w-64 bg-gray-800 border-r border-gray-700 p-4">Assets</div>
        <div className="flex-1 bg-gray-900 p-4">Preview</div>
        <div className="w-80 bg-gray-800 border-l border-gray-700 p-4">Chat</div>
      </main>
    </div>
  )
}

export default App
```

- [ ] **Step 6: Verify build and test setup**

```bash
cd frontend && npm run build && npx vitest run
```

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with Vite, TypeScript, TailwindCSS, and Vitest"
```

---

## Task 2: TypeScript Types & REST API Client

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/hooks.ts`
- Test: `frontend/__tests__/api/client.test.ts`

- [ ] **Step 1: Define shared types**

```typescript
// frontend/src/types/index.ts
export interface Asset {
  asset_id: string
  filename: string
  content_type: string
  size: number
}

export interface Project {
  project_id: string
  name: string
  description: string
  created_at: string
  version: number
}

export interface ProjectCreate {
  name: string
  description?: string
}

export interface EffectPattern {
  id: number
  name: string
  description: string
  category: string
  tags: string
  confidence: number
  verified: boolean
}

export interface ChatMessage {
  type: 'user_message' | 'ai_message' | 'ai_thinking' | 'generation_start' | 'generation_progress' | 'generation_complete' | 'ai_question' | 'error'
  content: string
  task?: string
  progress?: number
  preview_url?: string
  question_id?: string
  code?: string
  message?: string
}

export interface ExampleEntry {
  title: string
  type: string
  tags: string[]
  path: string
  object_count: number
  summary: string
}
```

- [ ] **Step 2: Create REST API client**

```typescript
// frontend/src/api/client.ts
const BASE_URL = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || res.statusText)
  }
  return res.json()
}

export const api = {
  // Projects
  listProjects: () => request<import('../types').Project[]>('/projects'),
  createProject: (data: import('../types').ProjectCreate) =>
    request<import('../types').Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProject: (id: string) => request<import('../types').Project>(`/projects/${id}`),
  exportProject: (id: string, targetDir: string) =>
    request<{ status: string }>(`/projects/${id}/export`, { method: 'POST', body: JSON.stringify({ target_dir: targetDir }) }),
  previewProject: (id: string) =>
    request<{ available: boolean; preview_url: string | null }>(`/projects/${id}/preview`, { method: 'POST' }),

  // Assets
  listAssets: () => request<import('../types').Asset[]>('/assets'),
  uploadAsset: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE_URL}/assets/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Upload failed')
    return res.json() as Promise<import('../types').Asset>
  },
  deleteAsset: (id: string) => request<{ status: string }>(`/assets/${id}`, { method: 'DELETE' }),

  // Knowledge
  listPatterns: (query?: string) =>
    request<import('../types').EffectPattern[]>(`/knowledge/patterns${query ? `?q=${query}` : ''}`),

  // Examples
  listExamples: () => request<import('../types').ExampleEntry[]>('/examples'),
  importExample: (path: string) =>
    request<import('../types').ExampleEntry>('/examples/import', { method: 'POST', body: JSON.stringify({ path }) }),

  // Config
  getConfig: () => request<Record<string, unknown>>('/config'),
  updateConfig: (data: Record<string, unknown>) =>
    request<Record<string, unknown>>('/config', { method: 'PUT', body: JSON.stringify(data) }),

  // Health
  health: () => request<{ status: string }>('/health'),
}
```

- [ ] **Step 3: Create React Query hooks**

```typescript
// frontend/src/api/hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { ProjectCreate } from '../types'

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: api.listProjects })
}

export function useProject(id: string) {
  return useQuery({ queryKey: ['project', id], queryFn: () => api.getProject(id), enabled: !!id })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectCreate) => api.createProject(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useAssets() {
  return useQuery({ queryKey: ['assets'], queryFn: api.listAssets })
}

export function useUploadAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.uploadAsset(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assets'] }),
  })
}

export function useDeleteAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteAsset(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assets'] }),
  })
}

export function usePatterns(query?: string) {
  return useQuery({ queryKey: ['patterns', query], queryFn: () => api.listPatterns(query) })
}

export function useExamples() {
  return useQuery({ queryKey: ['examples'], queryFn: api.listExamples })
}

export function usePreviewProject() {
  return useMutation({ mutationFn: (id: string) => api.previewProject(id) })
}
```

- [ ] **Step 4: Write tests**

```typescript
// frontend/__tests__/api/client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '../../src/api/client'

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches projects list', async () => {
    const mockProjects = [{ project_id: '1', name: 'Test', description: '', created_at: '', version: 1 }]
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockProjects),
    } as Response)

    const result = await api.listProjects()
    expect(result).toEqual(mockProjects)
  })

  it('creates a project', async () => {
    const mockProject = { project_id: '2', name: 'New', description: '', created_at: '', version: 1 }
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockProject),
    } as Response)

    const result = await api.createProject({ name: 'New' })
    expect(result.name).toBe('New')
  })

  it('throws on API error', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found',
      json: () => Promise.resolve({ detail: 'Not found' }),
    } as unknown as Response)

    await expect(api.getProject('999')).rejects.toThrow('Not found')
  })

  it('health check', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    } as Response)

    const result = await api.health()
    expect(result.status).toBe('ok')
  })
})
```

- [ ] **Step 5: Run tests**

```bash
cd frontend && npx vitest run __tests__/api/client.test.ts
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/ frontend/src/api/ frontend/__tests__/
git commit -m "feat: add TypeScript types, REST API client, and React Query hooks"
```

---

## Task 3: Zustand Stores (Project + Chat)

**Files:**
- Create: `frontend/src/stores/projectStore.ts`
- Create: `frontend/src/stores/chatStore.ts`
- Test: `frontend/__tests__/stores/projectStore.test.ts`
- Test: `frontend/__tests__/stores/chatStore.test.ts`

- [ ] **Step 1: Create project store**

```typescript
// frontend/src/stores/projectStore.ts
import { create } from 'zustand'

interface ProjectState {
  currentProjectId: string | null
  setCurrentProject: (id: string | null) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  currentProjectId: null,
  setCurrentProject: (id) => set({ currentProjectId: id }),
}))
```

- [ ] **Step 2: Create chat store**

```typescript
// frontend/src/stores/chatStore.ts
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
```

- [ ] **Step 3: Write tests**

```typescript
// frontend/__tests__/stores/projectStore.test.ts
import { describe, it, expect } from 'vitest'
import { useProjectStore } from '../../src/stores/projectStore'

describe('projectStore', () => {
  it('starts with no project selected', () => {
    const state = useProjectStore.getState()
    expect(state.currentProjectId).toBeNull()
  })

  it('sets current project', () => {
    useProjectStore.getState().setCurrentProject('1')
    expect(useProjectStore.getState().currentProjectId).toBe('1')
  })

  it('clears current project', () => {
    useProjectStore.getState().setCurrentProject('1')
    useProjectStore.getState().setCurrentProject(null)
    expect(useProjectStore.getState().currentProjectId).toBeNull()
  })
})
```

```typescript
// frontend/__tests__/stores/chatStore.test.ts
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
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npx vitest run __tests__/stores/
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/ frontend/__tests__/stores/
git commit -m "feat: add Zustand stores for project and chat state"
```

---

## Task 4: WebSocket Connection Manager

**Files:**
- Create: `frontend/src/api/websocket.ts`
- Test: `frontend/__tests__/api/websocket.test.ts`

- [ ] **Step 1: Implement WebSocket manager**

```typescript
// frontend/src/api/websocket.ts
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
```

- [ ] **Step 2: Write tests**

```typescript
// frontend/__tests__/api/websocket.test.ts
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
    vi.stubGlobal('WebSocket', vi.fn(() => mockWs))
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
```

- [ ] **Step 3: Run tests**

```bash
cd frontend && npx vitest run __tests__/api/websocket.test.ts
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/websocket.ts frontend/__tests__/api/websocket.test.ts
git commit -m "feat: add WebSocket connection manager with auto-reconnect"
```

---

## Task 5: UI Components — ChatPanel

**Files:**
- Create: `frontend/src/components/ChatPanel/ChatPanel.tsx`
- Create: `frontend/src/components/ChatPanel/MessageList.tsx`
- Create: `frontend/src/components/ChatPanel/ChatInput.tsx`
- Create: `frontend/src/components/common/Spinner.tsx`
- Test: `frontend/__tests__/components/ChatPanel.test.tsx`

- [ ] **Step 1: Create Spinner component**

```tsx
// frontend/src/components/common/Spinner.tsx
export function Spinner({ className = '' }: { className?: string }) {
  return (
    <div className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent ${className}`} />
  )
}
```

- [ ] **Step 2: Create MessageList**

```tsx
// frontend/src/components/ChatPanel/MessageList.tsx
import { useEffect, useRef } from 'react'
import { Spinner } from '../common/Spinner'
import type { ChatMessage } from '../../types'

interface Props {
  messages: ChatMessage[]
  isThinking: boolean
}

export function MessageList({ messages, isThinking }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {messages.filter(m => m.type === 'user_message' || m.type === 'ai_message').map((msg, i) => (
        <div key={i} className={`flex ${msg.type === 'user_message' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
            msg.type === 'user_message'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-100'
          }`}>
            {msg.content}
          </div>
        </div>
      ))}
      {isThinking && (
        <div className="flex justify-start">
          <div className="bg-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 flex items-center gap-2">
            <Spinner /> Thinking...
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
```

- [ ] **Step 3: Create ChatInput**

```tsx
// frontend/src/components/ChatPanel/ChatInput.tsx
import { useState, type KeyboardEvent } from 'react'

interface Props {
  onSend: (content: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('')

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="p-3 border-t border-gray-700">
      <div className="flex gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your wallpaper effect..."
          disabled={disabled}
          className="flex-1 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
          rows={2}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed self-end"
        >
          Send
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create ChatPanel**

```tsx
// frontend/src/components/ChatPanel/ChatPanel.tsx
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
```

- [ ] **Step 5: Write test**

```tsx
// frontend/__tests__/components/ChatPanel.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useChatStore } from '../../src/stores/chatStore'
import { useProjectStore } from '../../src/stores/projectStore'
import { MessageList } from '../../src/components/ChatPanel/MessageList'
import { ChatInput } from '../../src/components/ChatPanel/ChatInput'
import userEvent from '@testing-library/user-event'

describe('MessageList', () => {
  it('renders messages', () => {
    render(
      <MessageList
        messages={[
          { type: 'user_message', content: 'Hello' },
          { type: 'ai_message', content: 'Hi there!' },
        ]}
        isThinking={false}
      />
    )
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('shows thinking indicator', () => {
    render(<MessageList messages={[]} isThinking={true} />)
    expect(screen.getByText('Thinking...')).toBeInTheDocument()
  })
})

describe('ChatInput', () => {
  it('sends message on button click', async () => {
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)
    const textarea = screen.getByPlaceholderText(/describe/i)
    await userEvent.type(textarea, 'Add rain')
    await userEvent.click(screen.getByText('Send'))
    expect(onSend).toHaveBeenCalledWith('Add rain')
  })

  it('clears input after send', async () => {
    render(<ChatInput onSend={vi.fn()} />)
    const textarea = screen.getByPlaceholderText(/describe/i) as HTMLTextAreaElement
    await userEvent.type(textarea, 'Test')
    await userEvent.click(screen.getByText('Send'))
    expect(textarea.value).toBe('')
  })

  it('disables when disabled prop', () => {
    render(<ChatInput onSend={vi.fn()} disabled />)
    expect(screen.getByPlaceholderText(/describe/i)).toBeDisabled()
  })
})
```

- [ ] **Step 6: Run tests**

```bash
cd frontend && npx vitest run __tests__/components/ChatPanel.test.tsx
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ChatPanel/ frontend/src/components/common/ frontend/__tests__/components/ChatPanel.test.tsx
git commit -m "feat: add ChatPanel with message list, input, and WebSocket integration"
```

---

## Task 6: UI Components — AssetPanel

**Files:**
- Create: `frontend/src/components/AssetPanel/AssetPanel.tsx`
- Create: `frontend/src/components/AssetPanel/AssetUpload.tsx`
- Create: `frontend/src/components/AssetPanel/LayerTree.tsx`
- Test: `frontend/__tests__/components/AssetPanel.test.tsx`

- [ ] **Step 1: Create AssetUpload**

```tsx
// frontend/src/components/AssetPanel/AssetUpload.tsx
import { useCallback } from 'react'
import { useUploadAsset } from '../../api/hooks'

export function AssetUpload() {
  const upload = useUploadAsset()

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    files.forEach((file) => upload.mutate(file))
  }, [upload])

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach((file) => upload.mutate(file))
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="border-2 border-dashed border-gray-600 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition-colors"
    >
      <input
        type="file"
        onChange={handleFileSelect}
        className="hidden"
        id="asset-upload"
        multiple
        accept="image/*,video/*,audio/*,.pkg,.json"
      />
      <label htmlFor="asset-upload" className="cursor-pointer">
        <p className="text-sm text-gray-400">Drop files here or click to upload</p>
        <p className="text-xs text-gray-500 mt-1">Images, videos, audio, .pkg files</p>
      </label>
      {upload.isPending && <p className="text-xs text-blue-400 mt-2">Uploading...</p>}
    </div>
  )
}
```

- [ ] **Step 2: Create LayerTree**

```tsx
// frontend/src/components/AssetPanel/LayerTree.tsx
import type { Asset } from '../../types'
import { useDeleteAsset } from '../../api/hooks'

interface Props {
  assets: Asset[]
}

export function LayerTree({ assets }: Props) {
  const deleteAsset = useDeleteAsset()

  if (assets.length === 0) {
    return <p className="text-sm text-gray-500 py-2">No assets uploaded yet</p>
  }

  return (
    <ul className="space-y-1">
      {assets.map((asset) => (
        <li key={asset.asset_id} className="flex items-center justify-between group px-2 py-1 rounded hover:bg-gray-700">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs text-gray-400">
              {asset.content_type.startsWith('image') ? '🖼' : asset.content_type.startsWith('video') ? '🎬' : '📄'}
            </span>
            <span className="text-sm text-gray-200 truncate">{asset.filename}</span>
          </div>
          <button
            onClick={() => deleteAsset.mutate(asset.asset_id)}
            className="text-xs text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  )
}
```

- [ ] **Step 3: Create AssetPanel**

```tsx
// frontend/src/components/AssetPanel/AssetPanel.tsx
import { AssetUpload } from './AssetUpload'
import { LayerTree } from './LayerTree'
import { useAssets } from '../../api/hooks'

export function AssetPanel() {
  const { data: assets = [], isLoading } = useAssets()

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 border-b border-gray-700">
        <span className="text-sm font-medium">Assets & Layers</span>
      </div>
      <div className="p-3">
        <AssetUpload />
      </div>
      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <h3 className="text-xs font-medium text-gray-400 uppercase mb-2">Files</h3>
        {isLoading ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : (
          <LayerTree assets={assets} />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Write test**

```tsx
// frontend/__tests__/components/AssetPanel.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LayerTree } from '../../src/components/AssetPanel/LayerTree'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
)

describe('LayerTree', () => {
  it('shows empty message when no assets', () => {
    render(<LayerTree assets={[]} />, { wrapper })
    expect(screen.getByText(/no assets/i)).toBeInTheDocument()
  })

  it('renders asset list', () => {
    const assets = [
      { asset_id: '1', filename: 'bg.png', content_type: 'image/png', size: 1024 },
      { asset_id: '2', filename: 'rain.mp4', content_type: 'video/mp4', size: 2048 },
    ]
    render(<LayerTree assets={assets} />, { wrapper })
    expect(screen.getByText('bg.png')).toBeInTheDocument()
    expect(screen.getByText('rain.mp4')).toBeInTheDocument()
  })
})
```

- [ ] **Step 5: Run tests**

```bash
cd frontend && npx vitest run __tests__/components/AssetPanel.test.tsx
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/AssetPanel/ frontend/__tests__/components/AssetPanel.test.tsx
git commit -m "feat: add AssetPanel with drag-drop upload and layer tree"
```

---

## Task 7: UI Components — PreviewPanel & TopNav

**Files:**
- Create: `frontend/src/components/PreviewPanel/PreviewPanel.tsx`
- Create: `frontend/src/components/TopNav/TopNav.tsx`
- Test: `frontend/__tests__/components/PreviewPanel.test.tsx`

- [ ] **Step 1: Create PreviewPanel**

```tsx
// frontend/src/components/PreviewPanel/PreviewPanel.tsx
import { useProjectStore } from '../../stores/projectStore'
import { usePreviewProject } from '../../api/hooks'

export function PreviewPanel() {
  const projectId = useProjectStore((s) => s.currentProjectId)
  const preview = usePreviewProject()

  const handlePreview = () => {
    if (projectId) preview.mutate(projectId)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 border-b border-gray-700 flex items-center justify-between">
        <span className="text-sm font-medium">Preview</span>
        {projectId && (
          <button
            onClick={handlePreview}
            disabled={preview.isPending}
            className="text-xs px-3 py-1 bg-blue-600 rounded hover:bg-blue-500 disabled:opacity-50"
          >
            {preview.isPending ? 'Loading...' : 'Refresh Preview'}
          </button>
        )}
      </div>
      <div className="flex-1 flex items-center justify-center">
        {!projectId ? (
          <p className="text-gray-500 text-sm">Select a project to preview</p>
        ) : preview.data?.preview_url ? (
          <img src={preview.data.preview_url} alt="Wallpaper preview" className="max-w-full max-h-full object-contain" />
        ) : preview.data && !preview.data.available ? (
          <div className="text-center text-gray-500">
            <p className="text-sm">Wallpaper Engine not available</p>
            <p className="text-xs mt-1">Install WE for live preview</p>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Click "Refresh Preview" to render</p>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create TopNav**

```tsx
// frontend/src/components/TopNav/TopNav.tsx
import { useState } from 'react'
import { useProjects, useCreateProject } from '../../api/hooks'
import { useProjectStore } from '../../stores/projectStore'
import { useChatStore } from '../../stores/chatStore'

export function TopNav() {
  const { data: projects = [] } = useProjects()
  const createProject = useCreateProject()
  const { currentProjectId, setCurrentProject } = useProjectStore()
  const clearMessages = useChatStore((s) => s.clearMessages)
  const [showNew, setShowNew] = useState(false)
  const [newName, setNewName] = useState('')

  const handleCreate = () => {
    if (!newName.trim()) return
    createProject.mutate({ name: newName.trim() }, {
      onSuccess: (project) => {
        setCurrentProject(project.project_id)
        clearMessages()
        setNewName('')
        setShowNew(false)
      },
    })
  }

  const handleSelect = (id: string) => {
    setCurrentProject(id)
    clearMessages()
  }

  return (
    <header className="h-12 bg-gray-800 flex items-center px-4 border-b border-gray-700 gap-4">
      <h1 className="text-lg font-semibold whitespace-nowrap">AIMWallpaper</h1>

      <select
        value={currentProjectId || ''}
        onChange={(e) => handleSelect(e.target.value)}
        className="bg-gray-700 text-sm text-white rounded px-2 py-1 focus:outline-none"
      >
        <option value="">Select project...</option>
        {projects.map((p) => (
          <option key={p.project_id} value={p.project_id}>{p.name}</option>
        ))}
      </select>

      {showNew ? (
        <div className="flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Project name"
            className="bg-gray-700 text-sm text-white rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            autoFocus
          />
          <button onClick={handleCreate} className="text-xs px-2 py-1 bg-blue-600 rounded hover:bg-blue-500">Create</button>
          <button onClick={() => setShowNew(false)} className="text-xs px-2 py-1 bg-gray-600 rounded hover:bg-gray-500">Cancel</button>
        </div>
      ) : (
        <button onClick={() => setShowNew(true)} className="text-xs px-3 py-1 bg-blue-600 rounded hover:bg-blue-500">
          + New Project
        </button>
      )}
    </header>
  )
}
```

- [ ] **Step 3: Write test**

```tsx
// frontend/__tests__/components/PreviewPanel.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PreviewPanel } from '../../src/components/PreviewPanel/PreviewPanel'
import { useProjectStore } from '../../src/stores/projectStore'

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
)

describe('PreviewPanel', () => {
  it('shows placeholder when no project selected', () => {
    useProjectStore.getState().setCurrentProject(null)
    render(<PreviewPanel />, { wrapper })
    expect(screen.getByText(/select a project/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npx vitest run __tests__/components/PreviewPanel.test.tsx
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PreviewPanel/ frontend/src/components/TopNav/ frontend/__tests__/components/PreviewPanel.test.tsx
git commit -m "feat: add PreviewPanel and TopNav with project management"
```

---

## Task 8: Wire Up App.tsx with All Components

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Update main.tsx with providers**

```tsx
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
```

- [ ] **Step 2: Update App.tsx with all panels**

```tsx
// frontend/src/App.tsx
import { TopNav } from './components/TopNav/TopNav'
import { AssetPanel } from './components/AssetPanel/AssetPanel'
import { PreviewPanel } from './components/PreviewPanel/PreviewPanel'
import { ChatPanel } from './components/ChatPanel/ChatPanel'

function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <TopNav />
      <main className="flex-1 flex min-h-0">
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex-shrink-0">
          <AssetPanel />
        </aside>
        <section className="flex-1 min-w-0">
          <PreviewPanel />
        </section>
        <aside className="w-80 bg-gray-800 border-l border-gray-700 flex-shrink-0">
          <ChatPanel />
        </aside>
      </main>
    </div>
  )
}

export default App
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Run ALL frontend tests**

```bash
cd frontend && npx vitest run
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/main.tsx frontend/src/App.tsx
git commit -m "feat: wire up three-panel layout with all components and React Query provider"
```

---

## Summary

After completing all 8 tasks, you will have:

- **Project scaffold** — Vite + React 18 + TypeScript + TailwindCSS + Vitest
- **API layer** — REST client, React Query hooks, WebSocket connection manager
- **State management** — Zustand stores for project selection and chat state
- **ChatPanel** — Real-time AI conversation with message list, typing indicator, and input
- **AssetPanel** — Drag-and-drop upload, asset listing, delete
- **PreviewPanel** — WE preview display with refresh button, graceful degradation
- **TopNav** — Project selector, create new project
- **Three-panel layout** — Responsive layout wiring all components together

**Run the full stack:**
```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```
