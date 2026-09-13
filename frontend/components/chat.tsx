'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ChatList } from '@/components/chat-list'
import { ChatPanel } from '@/components/chat-panel'
import { EmptyScreen } from '@/components/empty-screen'
import { ChatScrollAnchor } from '@/components/chat-scroll-anchor'
import { type CodeAtlasMessage } from '@/lib/types'

const API_URL = 'http://localhost:5000'

export interface ChatProps extends React.ComponentProps<'div'> {
  repositoryId?: number
  conversationId?: number
}

export function Chat({
  repositoryId: initialRepositoryId,
  conversationId: initialConversationId,
  className
}: ChatProps) {
  const [repositoryId, setRepositoryId] = useState<number | null>(
    initialRepositoryId ?? null
  )
  const [conversationId, setConversationId] = useState<number | null>(
    initialConversationId ?? null
  )

  const [messages, setMessages] = useState<CodeAtlasMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function sendMessage(question: string) {
    if (!repositoryId || !question.trim() || isLoading) return

    setIsLoading(true)

    const userMessage: CodeAtlasMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question
    }

    setMessages(prev => [...prev, userMessage])

    try {
      let activeConversationId = conversationId

      if (!activeConversationId) {
        const conversationResponse = await fetch(
          `${API_URL}/conversations`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              repository_id: repositoryId
            })
          }
        )

        if (!conversationResponse.ok) {
          throw new Error('Failed to create conversation')
        }

        const conversation = await conversationResponse.json()

        activeConversationId = conversation.conversation_id
        setConversationId(activeConversationId)
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question,
          repository_id: repositoryId,
          conversation_id: activeConversationId
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get CodeAtlas response')
      }

      const data = await response.json()

      const assistantMessage: CodeAtlasMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.answer
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error(error)

      setMessages(prev => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content:
            'Sorry, I could not connect to CodeAtlas. Make sure the Flask backend is running.'
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function stop() {
    // The current Flask endpoint is non-streaming.
  }

  async function reload() {
    const lastUserMessage = [...messages]
      .reverse()
      .find(message => message.role === 'user')

    if (!lastUserMessage) return

    setMessages(prev => prev.slice(0, -1))
    await sendMessage(lastUserMessage.content)
  }

  return (
    <div className={cn('pb-[200px] pt-4 md:pt-10', className)}>
      {messages.length ? (
        <>
          <ChatList messages={messages} />
          <ChatScrollAnchor trackVisibility={isLoading} />
        </>
      ) : (
        <EmptyScreen setInput={setInput} />
      )}

      <ChatPanel
        isLoading={isLoading}
        stop={stop}
        reload={reload}
        messages={messages}
        input={input}
        setInput={setInput}
        onSubmit={sendMessage}
      />
    </div>
  )
}
