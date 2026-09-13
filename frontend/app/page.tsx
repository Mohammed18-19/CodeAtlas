'use client'

import { FormEvent, useState } from 'react'
import { Chat } from '@/components/chat'
import { CodeAtlasLogo } from '@/components/codeatlas-logo'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API_URL = '/api/codeatlas'

type GitHubRepository = {
  id: number
  name: string
  full_name: string
  html_url: string
  clone_url: string
  description: string | null
  language: string | null
  stargazers_count: number
  forks_count: number
  owner: {
    login: string | null
    avatar_url: string | null
  }
}

const capabilities = [
  {
    title: 'Repository understanding',
    description:
      'Analyze source files, structure, imports, classes, functions, and documentation.',
  },
  {
    title: 'Hybrid retrieval',
    description:
      'Combine semantic and keyword retrieval before reranking the most relevant code.',
  },
  {
    title: 'Grounded answers',
    description:
      'Answers are built from retrieved repository context with file and line references.',
  },
  {
    title: 'Persistent conversations',
    description:
      'Keep repository context available while exploring the codebase through chat.',
  },
]

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState('')
  const [repositoryId, setRepositoryId] = useState<number | null>(null)

  const [githubQuery, setGithubQuery] = useState('')
  const [githubResults, setGithubResults] = useState<GitHubRepository[]>([])
  const [githubOpen, setGithubOpen] = useState(false)
  const [githubLoading, setGithubLoading] = useState(false)

  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function searchGitHub() {
    const query = githubQuery.trim()

    if (!query) {
      setGithubResults([])
      return
    }

    setGithubLoading(true)
    setError('')

    try {
      const response = await fetch(
        `${API_URL}/github/search?q=${encodeURIComponent(query)}`,
        { cache: 'no-store' },
      )

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.error || 'GitHub search failed.')
      }

      setGithubResults(data.repositories || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'GitHub search failed.')
      setGithubResults([])
    } finally {
      setGithubLoading(false)
    }
  }

  async function analyzeRepository(url: string) {
    const cleanUrl = url.trim()

    if (!cleanUrl) {
      setError('Enter a GitHub repository URL.')
      return
    }

    setGithubOpen(false)
    setLoading(true)
    setError('')
    setStatus('Starting repository analysis...')

    try {
      const response = await fetch(`${API_URL}/repositories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: cleanUrl }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          data.error ||
            data.message ||
            'Could not start repository analysis.',
        )
      }

      if (!data.job_id) {
        throw new Error('The backend did not return an ingestion job.')
      }

      const jobId = data.job_id

      while (true) {
        await new Promise((resolve) => setTimeout(resolve, 1000))

        const statusResponse = await fetch(
          `${API_URL}/repositories/status/${jobId}`,
          { cache: 'no-store' },
        )

        const job = await statusResponse.json().catch(() => ({}))

        if (!statusResponse.ok) {
          throw new Error(
            job.error || 'Could not read repository analysis status.',
          )
        }

        if (job.message) {
          setStatus(job.message)
        } else if (job.phase) {
          setStatus(
            `${job.phase}${job.progress ? ` — ${job.progress}%` : ''}`,
          )
        }

        if (job.status === 'completed') {
          setRepositoryId(job.repository_id)
          setStatus('')
          break
        }

        if (job.status === 'failed') {
          throw new Error(job.error || 'Repository analysis failed.')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setStatus('')
    } finally {
      setLoading(false)
    }
  }

  async function connectRepository(event: FormEvent) {
    event.preventDefault()
    await analyzeRepository(repoUrl)
  }

  if (repositoryId) {
    return (
      <main className="min-h-screen bg-[#09070f] text-white">
        <header className="border-b border-white/10">
          <div className="mx-auto flex h-16 max-w-7xl items-center px-6">
            <CodeAtlasLogo />
          </div>
        </header>

        <Chat repositoryId={repositoryId} />
      </main>
    )
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[#09070f] text-white">
      <header className="border-b border-white/10">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <CodeAtlasLogo />

          <a
            href="https://github.com/Mohammed18-19/CodeAtlas"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-white/60 transition hover:text-white"
          >
            GitHub ↗
          </a>
        </div>
      </header>

      <section className="relative">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_20%,rgba(139,92,246,0.18),transparent_42%)]" />

        <div className="relative mx-auto max-w-5xl px-6 py-24 text-center md:py-32">
          <div className="mx-auto mb-6 inline-flex items-center rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs text-white/60">
            AI codebase intelligence
          </div>

          <h1 className="mx-auto max-w-4xl text-5xl font-semibold tracking-tight md:text-7xl">
            Understand your codebase
            <span className="block bg-gradient-to-r from-violet-300 via-purple-400 to-fuchsia-400 bg-clip-text text-transparent">
              through conversation.
            </span>
          </h1>

          <p className="mx-auto mt-7 max-w-2xl text-base leading-7 text-white/55 md:text-lg">
            Connect a GitHub repository, let CodeAtlas index its code and
            documentation, then ask questions grounded in the actual project.
          </p>

          <form
            onSubmit={connectRepository}
            className="mx-auto mt-10 flex max-w-2xl flex-col gap-3 sm:flex-row"
          >
            <Input
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              placeholder="https://github.com/owner/repository"
              disabled={loading}
              className="h-12 border-white/10 bg-white/[0.04] text-white placeholder:text-white/30"
            />

            <Button
              type="submit"
              disabled={loading}
              className="h-12 bg-white px-6 text-black hover:bg-white/90"
            >
              {loading ? 'Analyzing…' : 'Analyze repository'}
            </Button>
          </form>

          <button
            type="button"
            onClick={() => {
              setGithubOpen(true)
              setError('')
            }}
            disabled={loading}
            className="mt-4 text-sm text-violet-300 transition hover:text-violet-200 disabled:opacity-40"
          >
            Browse public GitHub repositories →
          </button>

          {status && (
            <p className="mt-4 text-sm text-white/50">
              {status}
            </p>
          )}

          {error && (
            <p className="mx-auto mt-4 max-w-2xl text-sm text-red-400">
              {error}
            </p>
          )}

          <div className="mx-auto mt-20 max-w-4xl rounded-2xl border border-white/10 bg-white/[0.025] p-2 shadow-2xl shadow-violet-950/20">
            <div className="rounded-xl border border-white/10 bg-[#0d0a16] p-6 text-left">
              <div className="mb-5 flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
              </div>

              <div className="grid gap-6 md:grid-cols-[180px_1fr]">
                <div className="space-y-2 border-r border-white/10 pr-5 text-xs text-white/40">
                  <p className="text-white/70">CodeAtlas</p>
                  <p>Repositories</p>
                  <p>Conversations</p>
                  <p>Search</p>
                </div>

                <div>
                  <p className="text-sm text-white/40">Repository question</p>
                  <p className="mt-2 text-lg text-white/90">
                    How does this request flow through the application?
                  </p>

                  <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.025] p-4">
                    <p className="text-sm leading-6 text-white/65">
                      CodeAtlas retrieves the relevant implementation,
                      follows the request path through the codebase, and
                      returns an answer with source references.
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {['app.py', 'ctx.py', 'routes.py'].map((file) => (
                        <span
                          key={file}
                          className="rounded-md bg-violet-500/10 px-2 py-1 text-xs text-violet-300"
                        >
                          {file}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-white/10">
        <div className="mx-auto max-w-5xl px-6 py-20">
          <div className="mb-12 max-w-xl">
            <p className="text-sm text-violet-300">How it works</p>
            <h2 className="mt-3 text-3xl font-semibold">
              From repository to useful answers.
            </h2>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            {[
              ['01', 'Connect', 'Provide a GitHub repository URL or browse public repositories.'],
              ['02', 'Index', 'CodeAtlas parses and indexes the repository.'],
              ['03', 'Explore', 'Ask questions and inspect grounded results.'],
            ].map(([number, title, description]) => (
              <div
                key={number}
                className="rounded-2xl border border-white/10 bg-white/[0.025] p-6"
              >
                <span className="text-xs text-white/30">{number}</span>
                <h3 className="mt-8 text-lg font-medium">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-white/45">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="mx-auto max-w-5xl px-6 py-20">
          <div className="mb-12 max-w-xl">
            <p className="text-sm text-violet-300">Built for code</p>
            <h2 className="mt-3 text-3xl font-semibold">
              Useful repository intelligence, without the noise.
            </h2>
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            {capabilities.map((capability) => (
              <div
                key={capability.title}
                className="rounded-2xl border border-white/10 bg-white/[0.025] p-7"
              >
                <h3 className="text-lg font-medium">{capability.title}</h3>
                <p className="mt-3 text-sm leading-6 text-white/45">
                  {capability.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-6 py-10 text-sm text-white/35 sm:flex-row sm:items-center sm:justify-between">
          <span>CodeAtlas — AI codebase intelligence</span>
          <a
            href="https://github.com/Mohammed18-19/CodeAtlas"
            target="_blank"
            rel="noreferrer"
            className="transition hover:text-white"
          >
            Source on GitHub ↗
          </a>
        </div>
      </footer>

      {githubOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) {
              setGithubOpen(false)
            }
          }}
        >
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-[#100c18] shadow-2xl">
            <div className="border-b border-white/10 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold">
                    Browse GitHub repositories
                  </h2>
                  <p className="mt-1 text-sm text-white/40">
                    Search public repositories and analyze one directly.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setGithubOpen(false)}
                  className="text-white/40 transition hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="mt-5 flex gap-2">
                <Input
                  value={githubQuery}
                  onChange={(event) => setGithubQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault()
                      void searchGitHub()
                    }
                  }}
                  placeholder="Search GitHub, e.g. flask python"
                  className="border-white/10 bg-white/[0.04] text-white placeholder:text-white/30"
                />

                <Button
                  type="button"
                  onClick={() => void searchGitHub()}
                  disabled={githubLoading || !githubQuery.trim()}
                  className="bg-white text-black hover:bg-white/90"
                >
                  {githubLoading ? 'Searching…' : 'Search'}
                </Button>
              </div>
            </div>

            <div className="max-h-[55vh] overflow-y-auto p-5">
              {githubResults.length === 0 && !githubLoading && (
                <div className="py-10 text-center text-sm text-white/35">
                  Search for a public GitHub repository.
                </div>
              )}

              <div className="space-y-3">
                {githubResults.map((repo) => (
                  <div
                    key={repo.id}
                    className="rounded-xl border border-white/10 bg-white/[0.025] p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-white">
                          {repo.full_name}
                        </p>

                        <p className="mt-1 line-clamp-2 text-sm leading-5 text-white/40">
                          {repo.description || 'No description provided.'}
                        </p>

                        <div className="mt-3 flex flex-wrap gap-3 text-xs text-white/35">
                          {repo.language && <span>{repo.language}</span>}
                          <span>★ {repo.stargazers_count.toLocaleString()}</span>
                          <span>⑂ {repo.forks_count.toLocaleString()}</span>
                        </div>
                      </div>

                      <div className="flex shrink-0 gap-2">
                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/50 transition hover:text-white"
                        >
                          GitHub
                        </a>

                        <Button
                          type="button"
                          onClick={() => void analyzeRepository(repo.clone_url)}
                          disabled={loading}
                          className="bg-white text-black hover:bg-white/90"
                        >
                          Analyze
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
