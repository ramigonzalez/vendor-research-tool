import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ResearchResults } from '../../lib/types'

interface ExecutiveSummaryProps {
  results: ResearchResults
}

export function ExecutiveSummary({ results }: ExecutiveSummaryProps) {
  const { summary, rankings } = results
  const sortedRankings = [...(rankings || [])].sort((a, b) => a.rank - b.rank)
  const [viewMode, setViewMode] = useState<'rendered' | 'source'>('rendered')
  const maxScore = sortedRankings.length > 0 ? sortedRankings[0].overall_score : 100

  return (
    <div className="mb-5 p-5 bg-bg-secondary rounded-sm shadow-sm max-w-[750px]">
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

      {sortedRankings.length > 0 && (
        <>
          <h3 className="text-lg font-semibold mt-4 mb-2">Rankings</h3>
          <ol className="list-none p-0 m-0">
            {sortedRankings.map(r => {
              const isFirst = r.rank === 1
              const barWidth = maxScore > 0 ? (r.overall_score / maxScore) * 100 : 0
              return (
                <li
                  key={r.vendor}
                  className={`py-2.5 px-3 my-1.5 rounded-xs text-sm flex items-center gap-3 ${
                    isFirst
                      ? 'bg-accent-primary/10 border border-accent-primary/30'
                      : 'bg-bg-primary'
                  }`}
                >
                  <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold shrink-0 ${
                    isFirst
                      ? 'bg-accent-primary text-white'
                      : 'bg-text-tertiary/20 text-text-secondary'
                  }`}>
                    #{r.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2">
                      <strong className="text-text-primary">{r.vendor}</strong>
                      <span className="font-mono text-xs text-text-secondary">{r.overall_score.toFixed(1)}/100</span>
                    </div>
                    <div className="h-1.5 mt-1 bg-border-default rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isFirst ? 'bg-accent-primary' : 'bg-text-tertiary'}`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                </li>
              )
            })}
          </ol>
        </>
      )}
    </div>
  )
}
