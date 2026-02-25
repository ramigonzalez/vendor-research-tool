import type { ResearchResults } from '../../lib/types'
import { PRIORITY_WEIGHTS } from '../../lib/scoring'

interface PriorityWeightsProps {
  results: ResearchResults
}

const priorityColors: Record<string, string> = {
  high: 'bg-confidence-high',
  medium: 'bg-confidence-medium',
  low: 'bg-confidence-low',
}

const priorityLabels: Record<string, string> = {
  high: 'H',
  medium: 'M',
  low: 'L',
}

export function PriorityWeights({ results }: PriorityWeightsProps) {
  const { rankings, requirements } = results

  if (!rankings || rankings.length === 0) return null

  const sortedRankings = [...rankings].sort((a, b) => a.rank - b.rank)

  return (
    <div className="mt-4">
      {/* Priority Legend */}
      <div className="flex items-center gap-4 mb-3 text-xs text-text-secondary">
        <strong>Priority Weights:</strong>
        {Object.entries(PRIORITY_WEIGHTS).map(([key, weight]) => (
          <span key={key} className="inline-flex items-center gap-1">
            <span className={`inline-block w-5 h-5 rounded-xs text-white text-center leading-5 text-[10px] font-bold ${priorityColors[key]}`}>
              {priorityLabels[key]}
            </span>
            {key} = {weight}&times;
          </span>
        ))}
      </div>

      {/* Ranking Formula */}
      <div className="text-xs text-text-tertiary mb-3">
        <strong>Ranking formula:</strong>{' '}
        <code className="bg-bg-code-block px-1.5 py-0.5 rounded-xs font-mono">
          &Sigma;(score &times; confidence &times; priority_weight) / max_possible &times; 100
        </code>
      </div>

      {/* Per-vendor breakdown */}
      <details className="text-xs">
        <summary className="cursor-pointer text-text-link hover:underline mb-2">
          Show per-vendor ranking breakdown
        </summary>
        <div className="space-y-2 pl-2">
          {sortedRankings.map(r => {
            const vendorScores = results.matrix[r.vendor]
            if (!vendorScores) return null

            return (
              <div key={r.vendor} className="bg-bg-primary p-2 rounded-xs">
                <div className="font-medium text-text-primary mb-1">
                  #{r.rank} {r.vendor} &mdash; {r.overall_score.toFixed(1)}/100
                </div>
                <div className="space-y-0.5">
                  {requirements.map(req => {
                    const score = vendorScores[req.id]
                    if (!score) return null
                    const weight = PRIORITY_WEIGHTS[req.priority] || 1
                    const contribution = score.score * score.confidence * weight
                    return (
                      <div key={req.id} className="flex items-center gap-2 text-text-tertiary">
                        <span className={`inline-block w-4 h-4 rounded-xs text-white text-center leading-4 text-[9px] font-bold ${priorityColors[req.priority]}`}>
                          {priorityLabels[req.priority]}
                        </span>
                        <span className="flex-1 truncate">{req.id}</span>
                        <span>{score.score.toFixed(1)} &times; {score.confidence.toFixed(2)} &times; {weight} = {contribution.toFixed(1)}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </details>
    </div>
  )
}
