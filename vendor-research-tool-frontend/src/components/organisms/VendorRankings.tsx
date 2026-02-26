import type { VendorRanking } from '../../lib/types'

interface VendorRankingsProps {
  rankings: VendorRanking[]
}

export function VendorRankings({ rankings }: VendorRankingsProps) {
  if (!rankings || rankings.length === 0) return null

  const sortedRankings = [...rankings].sort((a, b) => a.rank - b.rank)

  return (
    <div className="bg-bg-secondary rounded-sm shadow-sm border border-border-subtle p-6">
      <h2 className="text-xl font-heading font-semibold mb-3 text-text-primary">Vendor Rankings</h2>
      <ol className="list-none p-0 m-0 space-y-2">
        {sortedRankings.map(r => {
          const isFirst = r.rank === 1
          const barWidth = r.overall_score
          return (
            <li
              key={r.vendor}
              className={`py-3 px-4 rounded-xs flex items-center gap-3 ${
                isFirst
                  ? 'bg-accent-primary/10 border border-accent-primary/30'
                  : 'bg-bg-primary border border-border-subtle'
              }`}
            >
              <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold shrink-0 ${
                isFirst
                  ? 'bg-accent-primary text-white'
                  : 'bg-text-tertiary/20 text-text-secondary'
              }`}>
                #{r.rank}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <strong className="text-base text-text-primary">{r.vendor}</strong>
                  <span className="font-mono text-xs text-text-secondary">{r.overall_score.toFixed(1)}/100</span>
                </div>
                <div className="h-2 mt-1 bg-border-default rounded-full overflow-hidden">
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
    </div>
  )
}
