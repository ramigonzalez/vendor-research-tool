import { useState } from 'react'
import type { ResearchResults } from '../../lib/types'
import { PRIORITY_WEIGHTS } from '../../lib/scoring'
import { Badge } from '../atoms/Badge'

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
  const [isExpanded, setIsExpanded] = useState(false)

  if (!rankings || rankings.length === 0) return null

  const sortedRankings = [...rankings].sort((a, b) => a.rank - b.rank)

  return (
    <div className="border border-border-default rounded-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        className="w-full text-left px-4 py-3 bg-bg-secondary hover:bg-bg-primary transition-colors rounded-sm text-sm font-medium text-text-primary flex items-center justify-between cursor-pointer border-none"
      >
        <span>Ranking Breakdown</span>
        <span className="text-text-tertiary">{isExpanded ? '\u25B2' : '\u25BC'}</span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 bg-bg-secondary rounded-b-sm space-y-4">
          {/* Priority Weights + Formula */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary pt-2">
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

          <div className="text-xs text-text-tertiary">
            <strong>Ranking formula:</strong>{' '}
            <code className="bg-bg-code-block px-1.5 py-0.5 rounded-xs font-mono">
              &Sigma;(score &times; confidence &times; priority_weight) / max_possible &times; 100
            </code>
          </div>

          {/* Per-vendor breakdown */}
          <div className="space-y-3">
            {sortedRankings.map(r => {
              const vendorScores = results.matrix[r.vendor]
              if (!vendorScores) return null

              return (
                <div key={r.vendor} className="border border-border-subtle rounded-sm p-3 bg-bg-primary">
                  <div className="font-medium text-text-primary mb-2 flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-accent-primary text-white text-xs font-bold">
                      #{r.rank}
                    </span>
                    <span>{r.vendor}</span>
                    <span className="text-text-secondary">&mdash; {r.overall_score.toFixed(1)}/100</span>
                  </div>
                  <div className="space-y-1">
                    {requirements.map(req => {
                      const score = vendorScores[req.id]
                      if (!score) return null
                      const weight = PRIORITY_WEIGHTS[req.priority] || 1
                      const contribution = score.score * score.confidence * weight
                      return (
                        <div key={req.id} className="flex items-center gap-2 text-text-secondary" title={req.description}>
                          <Badge variant="priority">{priorityLabels[req.priority]}</Badge>
                          <span className="font-mono text-xs shrink-0">{req.id}</span>
                          <span className="text-xs truncate flex-1">&mdash; {req.description}</span>
                          <span className="text-xs shrink-0 font-mono">{score.score.toFixed(1)} &times; {score.confidence.toFixed(2)} &times; {weight} = {contribution.toFixed(1)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
