import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Spinner } from '../../src/components/common/Spinner'

describe('Spinner', () => {
  it('renders a spinner element', () => {
    const { container } = render(<Spinner />)
    const spinner = container.firstElementChild
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('animate-spin')
  })

  it('applies custom className', () => {
    const { container } = render(<Spinner className="text-blue-400" />)
    expect(container.firstElementChild).toHaveClass('text-blue-400')
  })
})
