import type { Asset, Project, ProjectCreate, EffectPattern, ExampleEntry } from '../types'

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
  listProjects: () => request<Project[]>('/projects'),
  createProject: (data: ProjectCreate) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  exportProject: (id: string, targetDir: string) =>
    request<{ status: string }>(`/projects/${id}/export`, { method: 'POST', body: JSON.stringify({ target_dir: targetDir }) }),
  previewProject: (id: string) =>
    request<{ available: boolean; preview_url: string | null }>(`/projects/${id}/preview`, { method: 'POST' }),

  // Assets
  listAssets: () => request<Asset[]>('/assets'),
  uploadAsset: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE_URL}/assets/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Upload failed')
    return res.json() as Promise<Asset>
  },
  deleteAsset: (id: string) => request<{ status: string }>(`/assets/${id}`, { method: 'DELETE' }),

  // Knowledge
  listPatterns: (query?: string) =>
    request<EffectPattern[]>(`/knowledge/patterns${query ? `?q=${query}` : ''}`),

  // Examples
  listExamples: () => request<ExampleEntry[]>('/examples'),
  importExample: (path: string) =>
    request<ExampleEntry>('/examples/import', { method: 'POST', body: JSON.stringify({ path }) }),

  // Config
  getConfig: () => request<Record<string, unknown>>('/config'),
  updateConfig: (data: Record<string, unknown>) =>
    request<Record<string, unknown>>('/config', { method: 'PUT', body: JSON.stringify(data) }),

  // Health
  health: () => request<{ status: string }>('/health'),
}
