'use client'

import { Button } from '@/components/ui/button'
import { IconArrowRight } from '@/components/ui/icons'
import { CodeAtlasLogo } from '@/components/codeatlas-logo'

const exampleMessages = [
  {
    heading: 'Understand the architecture',
    message: 'Explain the architecture of this repository.'
  },
  {
    heading: 'Find a specific implementation',
    message: 'Where is the database connection configured?'
  },
  {
    heading: 'Trace a feature',
    message: 'How does authentication flow through this codebase?'
  }
]

interface EmptyScreenProps {
  setInput: (value: string) => void
}

export function EmptyScreen({
  setInput
}: EmptyScreenProps) {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-10rem)] w-full max-w-4xl flex-col items-center justify-center px-4 pb-24 pt-8">

      <CodeAtlasLogo className="mb-5 h-24 w-24 drop-shadow-[0_0_30px_rgba(139,92,246,0.35)]" />

      <h1 className="text-center text-5xl font-semibold tracking-tight text-white">
        Code<span className="text-violet-400">Atlas</span>
      </h1>

      <p className="mt-5 max-w-2xl text-center text-base leading-7 text-zinc-400">
        Ask questions about your codebase and get grounded answers with source-file and line citations.
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {exampleMessages.map((message, index) => (
          <Button
            key={index}
            variant="outline"
            className="rounded-full border-violet-500/40 bg-violet-500/5 px-5 text-violet-200 hover:bg-violet-500/15 hover:text-white"
            onClick={() => setInput(message.message)}
          >
            <IconArrowRight className="mr-2 text-violet-300" />
            {message.heading}
          </Button>
        ))}
      </div>

    </div>
  )
}
