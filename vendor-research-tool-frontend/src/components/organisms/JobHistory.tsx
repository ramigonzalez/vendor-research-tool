import { useCallback, useEffect, useState } from 'react'
import type { ResearchJob } from '../../lib/types'
import { apiFetch } from '../../lib/api'
import { Badge } from '../atoms/Badge'

interface JobHistoryProps {
  onViewResults: (jobId: string) => void
}

export function JobHistory({ onViewResults }: JobHistoryProps) {
  const [jobs, setJobs] = useState<ResearchJob[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const loadJobs = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<ResearchJob[]>('/api/jobs')
      setJobs(data)
    } catch {
      setJobs([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const toggle = () => {
    setIsOpen(!isOpen)
    if (!isOpen) loadJobs()
  }

  return (
    <div>
      <button
        onClick={toggle}
        className="w-full text-left px-4 py-3 bg-bg-secondary hover:bg-bg-primary transition-colors rounded-sm text-sm font-medium text-text-primary flex items-center justify-between cursor-pointer border border-border-subtle"
      >
        Previous Runs
        <span className={`transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`}>&#9660;</span>
      </button>

      {isOpen && (
        <div className="mt-3">
          {loading && <p className="text-text-tertiary text-sm italic">Loading...</p>}

          {!loading && jobs.length === 0 && (
            <p className="text-text-tertiary text-sm italic py-2">
              No previous research runs. Click &ldquo;Run Research&rdquo; to start.
            </p>
          )}

          {!loading &&
            jobs.map(j => {
              const time = new Date(j.created_at).toLocaleString()
              const canView = j.status === 'completed'
              return (
                <div
                  key={j.id}
                  className="flex items-center gap-3 px-3.5 py-2.5 my-1 bg-bg-primary rounded-sm border border-border-subtle text-sm"
                >
                  <span className="text-text-secondary min-w-[160px]">{time}</span>
                  <Badge variant="status">{j.status}</Badge>
                  {canView && (
                    <button
                      onClick={() => onViewResults(j.id)}
                      className="bg-accent-primary text-white border-none px-3 py-1 rounded-xs cursor-pointer text-xs hover:bg-accent-primary-hover"
                    >
                      View Results
                    </button>
                  )}
                  {j.status === 'running' && (
                    <button disabled className="bg-text-tertiary text-white border-none px-3 py-1 rounded-xs text-xs cursor-not-allowed">
                      Running...
                    </button>
                  )}
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}
