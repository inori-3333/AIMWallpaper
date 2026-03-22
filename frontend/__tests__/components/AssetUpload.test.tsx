import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AssetUpload } from '../../src/components/AssetPanel/AssetUpload'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

const mockMutate = vi.fn()

vi.mock('../../src/api/hooks', () => ({
  useUploadAsset: () => ({ mutate: mockMutate, isPending: false }),
}))

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
)

function createFile(name: string, size = 1024, type = 'image/png'): File {
  const buffer = new ArrayBuffer(size)
  return new File([buffer], name, { type })
}

describe('AssetUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload area', () => {
    render(<AssetUpload />, { wrapper })
    expect(screen.getByText(/drop files here/i)).toBeInTheDocument()
  })

  it('shows error for unsupported file type via drag and drop', () => {
    render(<AssetUpload />, { wrapper })
    const dropZone = screen.getByText(/drop files here/i).closest('div')!

    const file = createFile('test.exe', 1024, 'application/x-msdownload')
    const dataTransfer = { files: [file] }

    fireEvent.drop(dropZone, { dataTransfer })

    expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument()
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('uploads valid file without error', async () => {
    render(<AssetUpload />, { wrapper })
    const input = document.getElementById('asset-upload') as HTMLInputElement

    const file = createFile('bg.png', 1024, 'image/png')
    await userEvent.upload(input, file)

    expect(mockMutate).toHaveBeenCalledWith(file)
    expect(screen.queryByText(/unsupported/i)).not.toBeInTheDocument()
  })

  it('shows allowed formats hint', () => {
    render(<AssetUpload />, { wrapper })
    expect(screen.getByText(/\.png/)).toBeInTheDocument()
    expect(screen.getByText(/\.mp4/)).toBeInTheDocument()
  })
})
