import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PreviewPanel } from '../../src/components/PreviewPanel/PreviewPanel'
import { useProjectStore } from '../../src/stores/projectStore'
import type { ReactNode } from 'react'

const wrapper = ({ children }: { children: ReactNode }) => (
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
