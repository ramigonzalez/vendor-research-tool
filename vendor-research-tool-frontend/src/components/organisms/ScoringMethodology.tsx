import { useState } from 'react'

interface WeightBarProps {
  label: string
  weight: number
  color: string
}

function WeightBar({ label, weight, color }: WeightBarProps) {
  return (
    <div className="flex items-center gap-2 text-xs mb-1">
      <span className="w-28 text-text-secondary">{label}</span>
      <div className="flex-1 h-3 bg-border-default rounded-xs overflow-hidden">
        <div className={`h-full rounded-xs ${color}`} style={{ width: `${weight * 100}%` }} />
      </div>
      <span className="w-10 text-right text-text-tertiary">{(weight * 100).toFixed(0)}%</span>
    </div>
  )
}

export function ScoringMethodology() {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="mb-5 border border-border-default rounded-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        className="w-full text-left px-4 py-3 bg-bg-secondary hover:bg-bg-primary transition-colors rounded-sm text-sm font-medium text-text-primary flex items-center justify-between cursor-pointer border-none"
      >
        <span>How scores are calculated</span>
        <span className="text-text-tertiary">{isExpanded ? '\u25B2' : '\u25BC'}</span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 bg-bg-secondary rounded-b-sm">
          {/* Score Formula */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold mb-2">Score (0&ndash;10)</h4>
            <p className="text-xs text-text-secondary mb-2">
              Each vendor-requirement pair is scored using a weighted formula:
            </p>
            <code className="block bg-bg-code-block px-3 py-2 rounded-xs text-xs font-mono text-text-primary mb-2">
              Score = Capability (40%) + Evidence (30%) + Maturity (20%) &minus; Limitations (10%)
            </code>
            <WeightBar label="Capability" weight={0.40} color="bg-accent-primary" />
            <WeightBar label="Evidence" weight={0.30} color="bg-accent-tertiary" />
            <WeightBar label="Maturity" weight={0.20} color="bg-status-analyzing" />
            <WeightBar label="Limitations" weight={0.10} color="bg-status-error" />

            <div className="mt-2 text-xs text-text-tertiary space-y-1">
              <p><strong>Capability levels:</strong> Full (10) &bull; Partial (7) &bull; Minimal (3) &bull; None (0) &bull; Unknown (2)</p>
              <p><strong>Maturity levels:</strong> GA (10) &bull; Beta (7) &bull; Experimental (4) &bull; Planned (2) &bull; Unknown (3)</p>
            </div>
          </div>

          {/* Confidence Formula */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold mb-2">Confidence (0&ndash;1)</h4>
            <p className="text-xs text-text-secondary mb-2">
              Confidence measures how reliable the score is, based on evidence quality:
            </p>
            <code className="block bg-bg-code-block px-3 py-2 rounded-xs text-xs font-mono text-text-primary mb-2">
              Confidence = Source Count (30%) + Authority (30%) + Recency (25%) + Consistency (15%)
            </code>
            <WeightBar label="Source Count" weight={0.30} color="bg-accent-primary" />
            <WeightBar label="Authority" weight={0.30} color="bg-accent-primary" />
            <WeightBar label="Recency" weight={0.25} color="bg-accent-tertiary" />
            <WeightBar label="Consistency" weight={0.15} color="bg-status-analyzing" />

            <div className="mt-2 text-xs text-text-tertiary space-y-1">
              <p><strong>Authority weights:</strong> Official docs (1.0) &bull; GitHub (0.8) &bull; Comparison (0.6) &bull; Blog (0.4) &bull; Community (0.3)</p>
              <p><strong>Recency:</strong> &le;180d (1.0) &bull; 180&ndash;365d (0.7) &bull; &gt;365d (0.3) &bull; No date (0.3)</p>
            </div>
          </div>

          {/* Ranking Formula */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Ranking (0&ndash;100)</h4>
            <p className="text-xs text-text-secondary mb-2">
              Vendors are ranked by weighted sum of scores across all requirements:
            </p>
            <code className="block bg-bg-code-block px-3 py-2 rounded-xs text-xs font-mono text-text-primary">
              Ranking = &Sigma;(score &times; confidence &times; priority_weight) / max_possible &times; 100
            </code>
            <div className="mt-2 text-xs text-text-tertiary">
              <p><strong>Priority weights:</strong> High = 3&times; &bull; Medium = 2&times; &bull; Low = 1&times;</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
