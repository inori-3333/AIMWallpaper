import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LayerTree } from '../../src/components/AssetPanel/LayerTree'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

const wrapper = ({ children }: { children: ReactNode }) => (
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
