'use client'

import Link from 'next/link'
import { CodeAtlasLogo } from '@/components/codeatlas-logo'
import { ThemeToggle } from '@/components/theme-toggle'
import { IconGitHub } from '@/components/ui/icons'

const navigation = [
  { label: 'New Chat', href: '/', icon: '✦', active: true },
  { label: 'Repositories', href: '/', icon: '⌘' },
  { label: 'Search', href: '/', icon: '⌕' },
  { label: 'History', href: '/', icon: '◷' },
]

export function Header() {
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
              className={
                item.active
                  ? 'flex items-center gap-3 rounded-xl border border-violet-500/20 bg-violet-500/[0.12] px-3.5 py-2.5 text-sm font-medium text-violet-200 shadow-[0_0_24px_rgba(124,58,237,0.08)]'
                  : 'flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm text-zinc-500 transition hover:bg-white/[0.04] hover:text-zinc-200'
              }
            >
              <span className="flex w-5 justify-center text-base">
                {item.icon}
              </span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="my-7 h-px bg-white/[0.07]" />

        <div className="px-1">
          <div className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
            Recent chats
          </div>

          <div className="rounded-xl px-3 py-2.5 text-sm text-zinc-500 transition hover:bg-white/[0.035] hover:text-zinc-300">
            <div className="truncate">
              Ask about your codebase
            </div>
            <div className="mt-1 text-[10px] text-zinc-700">
              No conversations yet
            </div>
          </div>
        </div>

        <div className="mt-auto border-t border-white/[0.07] pt-4">
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
