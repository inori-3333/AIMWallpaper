import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
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
