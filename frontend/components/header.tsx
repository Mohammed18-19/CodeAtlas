'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { CodeAtlasLogo } from '@/components/codeatlas-logo'
import { ThemeToggle } from '@/components/theme-toggle'
import { IconGitHub } from '@/components/ui/icons'

const API_URL = '/api/codeatlas'

type ConversationSummary = {
  id: number
  repository_id: number
  repository_name: string | null
  title: string
  created_at: string
}

const navigation = [
  { label: 'New Chat', href: '/?view=new', icon: '✦' },
  { label: 'Repositories', href: '/?view=repositories', icon: '⌘' },
  { label: 'Search', href: '/?view=search', icon: '⌕' },
  { label: 'History', href: '/?view=history', icon: '◷' },
]

export function Header() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])

  useEffect(() => {
    async function loadConversations() {
      try {
        const response = await fetch(`${API_URL}/conversations`, {
          cache: 'no-store'
        })

        if (!response.ok) return

        const data = await response.json()
        setConversations((data.conversations || []).slice(0, 5))
      } catch (error) {
        console.error('Failed to load recent conversations:', error)
      }
    }

    void loadConversations()
  }, [])

  return (
    <aside className="fixed inset-y-0 left-0 z-50 hidden w-[260px] border-r border-white/[0.07] bg-[#080812] lg:flex lg:flex-col">
      <div className="flex h-full flex-col px-4 py-5">
        <Link href="/" className="mb-8 flex items-center gap-3 px-2">
          <CodeAtlasLogo className="h-9 w-9" />

          <div>
            <div className="text-[17px] font-semibold tracking-tight text-white">
              Code<span className="text-violet-400">Atlas</span>
            </div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">
              AI Code Intelligence
            </div>
          </div>
        </Link>

        <nav className="space-y-1">
          {navigation.map(item => (
            <Link
              key={item.label}
              href={item.href}
              className="flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm text-zinc-500 transition hover:bg-white/[0.04] hover:text-zinc-200"
            >
              <span className="flex w-5 justify-center text-base">
                {item.icon}
              </span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="my-7 h-px bg-white/[0.07]" />

        <div className="flex min-h-0 flex-1 flex-col px-1">
          <div className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
            Recent chats
          </div>

          <div className="min-h-0 flex-1 space-y-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <div className="rounded-xl px-3 py-2.5 text-sm text-zinc-600">
                No conversations yet
              </div>
            ) : (
              conversations.map(conversation => (
                <Link
                  key={conversation.id}
                  href={`/?view=chat&repository=${conversation.repository_id}&conversation=${conversation.id}`}
                  className="block rounded-xl px-3 py-2.5 transition hover:bg-white/[0.04]"
                >
                  <div className="truncate text-sm text-zinc-400 hover:text-zinc-200">
                    {conversation.title || 'New Conversation'}
                  </div>
                  <div className="mt-1 truncate text-[10px] text-zinc-600">
                    {conversation.repository_name || 'Repository'}
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        <div className="mt-4 border-t border-white/[0.07] pt-4">
          <div className="flex items-center justify-between px-1">
            <ThemeToggle />

            <a
              target="_blank"
              href="https://github.com/Mohammed18-19/CodeAtlas"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-zinc-500 transition hover:bg-white/[0.04] hover:text-zinc-200"
            >
              <IconGitHub className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
      </div>
    </aside>
  )
}
