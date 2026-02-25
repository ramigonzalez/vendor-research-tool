import type { ResearchResults } from '../../lib/types'

interface ExecutiveSummaryProps {
  results: ResearchResults
}

export function ExecutiveSummary({ results }: ExecutiveSummaryProps) {
  const { summary, rankings } = results
  const sortedRankings = [...(rankings || [])].sort((a, b) => a.rank - b.rank)

  return (
    <div className="mb-5 p-5 bg-bg-secondary rounded-sm shadow-sm max-w-[750px]">
      <h2 className="text-xl font-semibold text-text-primary mt-0 mb-3">Executive Summary</h2>

      {!summary ? (
        <p className="text-text-tertiary italic">
          Executive summary not available — see matrix for detailed scores.
        </p>
      ) : (
        summary
          .split('\n\n')
          .filter(p => p.trim())
          .map((p, i) => (
            <p key={i} className="text-sm leading-relaxed text-text-primary mb-3">
              {p}
            </p>
          ))
      )}

      {sortedRankings.length > 0 && (
        <>
          <h3 className="text-lg font-semibold mt-4 mb-2">Rankings</h3>
          <ol className="list-none p-0 m-0">
            {sortedRankings.map(r => (
              <li key={r.vendor} className="py-2 px-3 my-1 bg-bg-primary rounded-xs text-sm">
                <strong>#{r.rank} {r.vendor}</strong> — {r.overall_score.toFixed(1)}/100
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  )
}
