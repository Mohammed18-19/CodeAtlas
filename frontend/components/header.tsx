'use client'

import Link from 'next/link'

import { ThemeToggle } from '@/components/theme-toggle'
import { CodeAtlasLogo } from '@/components/codeatlas-logo'
import { IconGitHub } from '@/components/ui/icons'

export function Header() {
  return (
    <aside className="fixed inset-y-0 left-0 z-50 hidden w-64 border-r border-white/10 bg-[#070711] lg:flex lg:flex-col">
      <div className="flex h-full flex-col px-4 py-5">

        <Link
          href="/"
          className="mb-8 flex items-center gap-3 px-2"
        >
          <CodeAtlasLogo className="h-9 w-9" />

          <span className="text-xl font-semibold tracking-tight text-white">
            Repo<span className="text-violet-400">Mind</span>
          </span>
        </Link>

        <nav className="space-y-2">

          <Link
            href="/"
            className="flex items-center rounded-xl bg-violet-600/20 px-4 py-3 text-sm font-medium text-violet-200 ring-1 ring-violet-500/20"
          >
            <span className="mr-3 text-lg text-violet-300">◌</span>
            New Chat
          </Link>

          <Link
            href="/"
            className="flex items-center rounded-xl px-4 py-3 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-zinc-100"
          >
            <span className="mr-3">⌘</span>
            Repositories
          </Link>

          <Link
            href="/"
            className="flex items-center rounded-xl px-4 py-3 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-zinc-100"
          >
            <span className="mr-3">⚙</span>
            Settings
          </Link>

        </nav>

        <div className="my-6 border-t border-white/10" />

        <div className="px-2">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">
            Recent Chats
          </p>

          <div className="rounded-lg px-2 py-2 text-sm text-zinc-400">
            <span className="mr-2">◌</span>
            What is the purpose of this...
          </div>
        </div>

        <div className="mt-auto flex items-center justify-between border-t border-white/10 pt-4">

          <ThemeToggle />

          <a
            target="_blank"
            href="https://github.com/Mohammed18-19/CodeAtlas"
            rel="noopener noreferrer"
            className="flex items-center rounded-lg px-3 py-2 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
          >
            <IconGitHub />

            <span className="ml-2">
              GitHub
            </span>
          </a>

        </div>
      </div>
    </aside>
  )
}
