import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ResearchResults } from '../../lib/types'

interface ExecutiveSummaryProps {
  results: ResearchResults
}

export function ExecutiveSummary({ results }: ExecutiveSummaryProps) {
  const { summary } = results
  const [viewMode, setViewMode] = useState<'rendered' | 'source'>('rendered')

  return (
    <div className="p-6 bg-bg-secondary rounded-sm shadow-sm border border-border-subtle">
      <h2 className="text-xl font-semibold text-text-primary mt-0 mb-3">Executive Summary</h2>

      {!summary ? (
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
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          ) : (
            <pre className="font-mono text-xs bg-bg-code-block p-3 rounded-sm whitespace-pre-wrap">{summary}</pre>
          )}
        </>
      )}

    </div>
  )
}
