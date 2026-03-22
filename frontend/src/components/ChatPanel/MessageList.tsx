import { useEffect, useRef } from 'react'
import { Spinner } from '../common/Spinner'
import type { ChatMessage } from '../../types'

interface Props {
  messages: ChatMessage[]
  isThinking: boolean
}

export function MessageList({ messages, isThinking }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {messages.filter(m => m.type === 'user_message' || m.type === 'ai_message').map((msg, i) => (
        <div key={i} className={`flex ${msg.type === 'user_message' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
            msg.type === 'user_message'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-100'
          }`}>
            {msg.content}
          </div>
        </div>
      ))}
      {isThinking && (
        <div className="flex justify-start">
          <div className="bg-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 flex items-center gap-2">
            <Spinner /> Thinking...
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
