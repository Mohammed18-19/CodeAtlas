'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import { ChatList } from '@/components/chat-list'
import { ChatPanel } from '@/components/chat-panel'
import { EmptyScreen } from '@/components/empty-screen'
import { ChatScrollAnchor } from '@/components/chat-scroll-anchor'
import { type CodeAtlasMessage } from '@/lib/types'

const API_URL = '/api/codeatlas'

export interface ChatProps extends React.ComponentProps<'div'> {
  repositoryId?: number
  conversationId?: number
  onConversationCreated?: (conversationId: number) => void
}

export function Chat({
  repositoryId: initialRepositoryId,
  conversationId: initialConversationId,
  className,
  onConversationCreated
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

  useEffect(() => {
    setRepositoryId(initialRepositoryId ?? null)
  }, [initialRepositoryId])

  useEffect(() => {
    setConversationId(initialConversationId ?? null)
  }, [initialConversationId])

  useEffect(() => {
    if (!initialConversationId) {
      setMessages([])
      return
    }

    let cancelled = false

    async function loadConversation() {
      try {
        const response = await fetch(
          `${API_URL}/conversations/${initialConversationId}`,
          { cache: 'no-store' }
        )

        if (!response.ok) {
          throw new Error('Failed to load conversation')
        }

        const conversation = await response.json()

        if (cancelled) return

        setRepositoryId(conversation.repository_id)
        setConversationId(conversation.id)

        setMessages(
          (conversation.messages || []).map(
            (message: {
              id: number
              role: 'user' | 'assistant'
              content: string
              created_at?: string
            }) => ({
              id: message.id,
              role: message.role,
              content: message.content,
              createdAt: message.created_at
            })
          )
        )

        localStorage.setItem(
          'codeatlas:last-session',
          JSON.stringify({
            repositoryId: conversation.repository_id,
            conversationId: conversation.id
          })
        )
      } catch (error) {
        console.error('Failed to load conversation:', error)
      }
    }

    void loadConversation()

    return () => {
      cancelled = true
    }
  }, [initialConversationId])

  useEffect(() => {
    if (!repositoryId) return

    const current = localStorage.getItem('codeatlas:last-session')
    const parsed = current ? JSON.parse(current) : {}

    localStorage.setItem(
      'codeatlas:last-session',
      JSON.stringify({
        ...parsed,
        repositoryId,
        ...(conversationId ? { conversationId } : {})
      })
    )
  }, [repositoryId, conversationId])

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

        localStorage.setItem(
          'codeatlas:last-session',
          JSON.stringify({
            repositoryId,
            conversationId: activeConversationId
          })
        )

        if (activeConversationId !== null) {
          onConversationCreated?.(activeConversationId)
        }
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
      <a
        href="/"
        className="mb-6 inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-500 transition hover:bg-white/[0.04] hover:text-zinc-200"
      >
        <span aria-hidden="true">←</span>
        Back to Home
      </a>
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
