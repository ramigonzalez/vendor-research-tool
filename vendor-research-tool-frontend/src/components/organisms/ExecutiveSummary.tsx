import { useCallback, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ResearchResults, SummaryFormat } from '../../lib/types'
import { regenerateSummary } from '../../lib/api'

const FORMAT_OPTIONS: { value: SummaryFormat; label: string }[] = [
  { value: 'formal', label: 'Formal' },
  { value: 'informal', label: 'Informal' },
  { value: 'concise', label: 'Concise' },
  { value: 'direct', label: 'Direct' },
]

interface ExecutiveSummaryProps {
  results: ResearchResults
  jobId: string | null
}

export function ExecutiveSummary({ results, jobId }: ExecutiveSummaryProps) {
  const { summary } = results
  const [viewMode, setViewMode] = useState<'rendered' | 'source'>('rendered')
  const [displaySummary, setDisplaySummary] = useState(summary)
  const [showFormats, setShowFormats] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Sync displaySummary when results.summary changes (e.g. new job loaded)
  useEffect(() => {
    setDisplaySummary(summary)
  }, [summary])

  // Auto-dismiss error after 5 seconds
  useEffect(() => {
    if (!error) return
    const timer = setTimeout(() => setError(null), 5000)
    return () => clearTimeout(timer)
  }, [error])

  // Close dropdown on outside click
  useEffect(() => {
    if (!showFormats) return
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowFormats(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showFormats])

  const handleFormatSelect = useCallback(
    async (format: SummaryFormat) => {
      if (!jobId) return
      setShowFormats(false)
      setIsRegenerating(true)
      setError(null)
      try {
        const res = await regenerateSummary(jobId, format)
        setDisplaySummary(res.summary)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to regenerate summary')
      } finally {
        setIsRegenerating(false)
      }
    },
    [jobId],
  )

  return (
    <div className="p-6 bg-bg-secondary rounded-sm shadow-sm border border-border-subtle">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-semibold text-text-primary m-0">Executive Summary</h2>

        {displaySummary && jobId && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowFormats((prev) => !prev)}
              disabled={isRegenerating}
              className={`px-3 py-1 text-xs rounded-sm border cursor-pointer transition-colors ${
                isRegenerating
                  ? 'bg-bg-primary text-text-tertiary border-border-default cursor-not-allowed'
                  : 'bg-bg-primary text-text-secondary border-border-default hover:border-border-focus'
              }`}
            >
              {isRegenerating ? 'Regenerating...' : 'Regenerate'}
            </button>

            {showFormats && (
              <div className="absolute right-0 top-full mt-1 bg-bg-secondary border border-border-default rounded-sm shadow-md z-10 min-w-[120px]">
                {FORMAT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleFormatSelect(opt.value)}
                    className="block w-full text-left px-3 py-1.5 text-xs text-text-secondary hover:bg-bg-primary hover:text-text-primary cursor-pointer transition-colors border-none bg-transparent"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mb-3 px-3 py-1.5 text-xs text-status-error bg-red-50 border border-status-error rounded-sm">
          {error}
        </div>
      )}

      {!displaySummary ? (
        <p className="text-text-tertiary italic">
          Executive summary not available — see matrix for detailed scores.
        </p>
      ) : (
        <>
          {/* View mode toggle */}
          <div className="flex gap-1 mb-3">
            <button
              onClick={() => setViewMode('rendered')}
              className={`px-3 py-1 text-xs rounded-sm border cursor-pointer transition-colors ${
                viewMode === 'rendered'
                  ? 'bg-accent-primary text-white border-accent-primary'
                  : 'bg-bg-primary text-text-secondary border-border-default hover:border-border-focus'
              }`}
            >
              Rendered
            </button>
            <button
              onClick={() => setViewMode('source')}
              className={`px-3 py-1 text-xs rounded-sm border cursor-pointer transition-colors ${
                viewMode === 'source'
                  ? 'bg-accent-primary text-white border-accent-primary'
                  : 'bg-bg-primary text-text-secondary border-border-default hover:border-border-focus'
              }`}
            >
              Source
            </button>
          </div>

          {viewMode === 'rendered' ? (
            <div className="font-body-ai text-sm leading-relaxed text-text-primary markdown-prose">
              <ReactMarkdown>{displaySummary}</ReactMarkdown>
            </div>
          ) : (
            <pre className="font-mono text-xs bg-bg-code-block p-3 rounded-sm whitespace-pre-wrap">{displaySummary}</pre>
          )}
        </>
      )}

    </div>
  )
}
