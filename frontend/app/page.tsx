'use client'

import { useState } from 'react'
import { Chat } from '@/components/chat'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API_URL = 'http://localhost:5000'

export default function IndexPage() {
  const [repoUrl, setRepoUrl] = useState('')
  const [repositoryId, setRepositoryId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  async function connectRepository(event: React.FormEvent) {
    event.preventDefault()

    if (!repoUrl.trim()) return

    setIsLoading(true)
    setError('')
    setStatus('Starting repository analysis...')

    try {
      const response = await fetch(`${API_URL}/repositories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          repo_url: repoUrl.trim()
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start repository analysis')
      }

      const data = await response.json()
      const jobId = data.job_id

      setStatus('Cloning and indexing repository...')

      while (true) {
        await new Promise(resolve => setTimeout(resolve, 1000))

        const statusResponse = await fetch(
          `${API_URL}/repositories/status/${jobId}`
        )

        if (!statusResponse.ok) {
          throw new Error('Failed to check repository status')
        }

        const statusData = await statusResponse.json()

        if (statusData.status === 'completed') {
          setRepositoryId(statusData.repository_id)
          setStatus('')
          break
        }

        if (statusData.status === 'failed') {
          throw new Error(
            statusData.error || 'Repository ingestion failed'
          )
        }

        setStatus('Cloning and indexing repository...')
      }
    } catch (error) {
      console.error(error)
      setError(
        error instanceof Error
              ? error.message
              : 'Could not analyze repository.'
      )
      setStatus('')
    } finally {
      setIsLoading(false)
    }
  }

  if (repositoryId) {
    return <Chat repositoryId={repositoryId} />
  }

  return (
    <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
      <div className="w-full max-w-2xl">
        <div className="rounded-xl border bg-background p-8 shadow-sm">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-semibold tracking-tight">
              Understand your codebase
            </h1>

            <p className="mt-3 text-muted-foreground">
              Connect a GitHub repository and ask CodeAtlas questions about
              its architecture, implementation, and code.
            </p>
          </div>

          <form onSubmit={connectRepository} className="space-y-4">
            <Input
              value={repoUrl}
              onChange={event => setRepoUrl(event.target.value)}
              placeholder="https://github.com/username/repository"
              disabled={isLoading}
            />

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !repoUrl.trim()}
            >
              {isLoading ? 'Analyzing repository...' : 'Analyze Repository'}
            </Button>
          </form>

          {status && (
            <p className="mt-4 text-sm text-muted-foreground">
              {status}
            </p>
          )}

          {error && (
            <p className="mt-4 text-sm text-destructive">
              {error}
            </p>
          )}
        </div>
      </div>
    </main>
  )
}
