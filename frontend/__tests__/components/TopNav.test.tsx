import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TopNav } from '../../src/components/TopNav/TopNav'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// Mock hooks
vi.mock('../../src/api/hooks', () => ({
  useProjects: () => ({ data: [{ project_id: 'p1', name: 'Test Project' }] }),
  useCreateProject: () => ({ mutate: vi.fn() }),
}))

vi.mock('../../src/stores/chatStore', () => ({
  useChatStore: (selector: (s: { clearMessages: () => void }) => unknown) =>
    selector({ clearMessages: vi.fn() }),
}))

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
)

describe('TopNav', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders brand name', () => {
    render(<TopNav />, { wrapper })
    expect(screen.getByText('AIMWallpaper')).toBeInTheDocument()
  })

  it('renders project selector with projects', () => {
    render(<TopNav />, { wrapper })
    expect(screen.getByText('Test Project')).toBeInTheDocument()
  })

  it('shows new project form when clicking + New Project', async () => {
    render(<TopNav />, { wrapper })
    await userEvent.click(screen.getByText('+ New Project'))
    expect(screen.getByPlaceholderText('Project name')).toBeInTheDocument()
  })

  it('hides new project form on cancel', async () => {
    render(<TopNav />, { wrapper })
    await userEvent.click(screen.getByText('+ New Project'))
    await userEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByPlaceholderText('Project name')).not.toBeInTheDocument()
  })
})
