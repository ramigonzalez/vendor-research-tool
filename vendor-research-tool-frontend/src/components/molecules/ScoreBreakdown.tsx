import type { ScoreResult } from '../../lib/types'
import { computeScoreBreakdown } from '../../lib/scoring'

interface ScoreBreakdownProps {
  scoreResult: ScoreResult
}

export function ScoreBreakdown({ scoreResult }: ScoreBreakdownProps) {
  const breakdown = computeScoreBreakdown(scoreResult)

  const components = [
    {
      label: 'Capability',
      weight: 0.40,
      rawScore: breakdown.capabilityScore,
      level: scoreResult.capability_level,
      contribution: 0.40 * breakdown.capabilityScore,
      positive: true,
    },
    {
      label: 'Evidence',
      weight: 0.30,
      rawScore: breakdown.evidenceScore,
      level: `${scoreResult.evidence.filter(e => e.supports_requirement).length} supporting`,
      contribution: 0.30 * breakdown.evidenceScore,
      positive: true,
    },
    {
      label: 'Maturity',
      weight: 0.20,
      rawScore: breakdown.maturityScore,
      level: scoreResult.maturity,
      contribution: 0.20 * breakdown.maturityScore,
      positive: true,
    },
    {
      label: 'Limitations',
      weight: 0.10,
      rawScore: breakdown.limitationsScore,
      level: `${scoreResult.limitations.length} limitation${scoreResult.limitations.length !== 1 ? 's' : ''}`,
      contribution: 0.10 * breakdown.limitationsScore,
      positive: breakdown.limitationsScore >= 6,
    },
  ]

  return (
    <div className="mt-3">
      <h4 className="text-sm font-semibold mb-2">
        Score Breakdown <span className="font-normal text-text-tertiary">({breakdown.total.toFixed(1)}/10)</span>
      </h4>

      <div className="space-y-1.5">
        {components.map(comp => (
          <div key={comp.label} className="flex items-center gap-2 text-xs">
            <span className="w-20 text-text-secondary">{comp.label}</span>
            <span className="w-8 text-text-tertiary text-right">{(comp.weight * 100).toFixed(0)}%</span>
            <span className="w-2 text-text-tertiary">&times;</span>
            <span className={`w-10 text-right font-mono ${comp.positive ? 'text-confidence-high' : 'text-confidence-low'}`}>
              {comp.rawScore.toFixed(1)}
            </span>
            <span className="text-text-tertiary text-[10px]">({comp.level})</span>
            <span className="ml-auto text-text-tertiary">=</span>
            <span className={`w-8 text-right font-mono ${comp.positive ? 'text-confidence-high' : 'text-confidence-low'}`}>
              {comp.contribution.toFixed(1)}
            </span>
          </div>
        ))}
      </div>

      {/* Visual formula */}
      <div className="mt-2 bg-bg-code-block px-3 py-2 rounded-xs text-xs font-mono text-text-primary">
        {components.map((comp, i) => (
          <span key={comp.label}>
            {i > 0 && ' + '}
            {comp.weight.toFixed(2)} &times; {comp.rawScore.toFixed(1)}
          </span>
        ))}
        <span> = <strong>{breakdown.total.toFixed(1)}</strong></span>
      </div>
    </div>
  )
}
