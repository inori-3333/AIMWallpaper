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
