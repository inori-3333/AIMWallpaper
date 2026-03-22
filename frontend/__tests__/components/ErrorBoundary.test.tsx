import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary } from '../../src/components/common/ErrorBoundary'

let shouldThrow = false

function ThrowingComponent() {
  if (shouldThrow) throw new Error('Test error')
  return <div>Working</div>
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    shouldThrow = false
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Hello</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders fallback UI on error', () => {
    shouldThrow = true
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    )
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Test error')).toBeInTheDocument()
  })

  it('renders custom fallback when provided', () => {
    shouldThrow = true
    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <ThrowingComponent />
      </ErrorBoundary>
    )
    expect(screen.getByText('Custom fallback')).toBeInTheDocument()
  })

  it('recovers after clicking Retry', async () => {
    shouldThrow = true
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    )
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()

    // Stop throwing before retry
    shouldThrow = false
    await userEvent.click(screen.getByText('Retry'))

    expect(screen.getByText('Working')).toBeInTheDocument()
  })
})
