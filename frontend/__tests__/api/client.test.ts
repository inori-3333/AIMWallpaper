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
