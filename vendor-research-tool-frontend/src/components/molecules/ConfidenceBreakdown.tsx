import { useState } from 'react'
import type { Evidence } from '../../lib/types'
import { computeConfidenceBreakdown } from '../../lib/scoring'

interface ConfidenceBreakdownProps {
  evidence: Evidence[]
}

interface SegmentInfo {
  key: string
  label: string
  weight: number
  value: number
  explanation: string
}

function getSegmentColor(value: number): string {
  if (value >= 0.7) return 'bg-confidence-high'
  if (value >= 0.4) return 'bg-confidence-medium'
  return 'bg-confidence-low'
}

export function ConfidenceBreakdown({ evidence }: ConfidenceBreakdownProps) {
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null)

  const breakdown = computeConfidenceBreakdown(evidence)

  const segments: SegmentInfo[] = [
    {
      key: 'sourceCount',
      label: 'Source Count',
      weight: 0.30,
      value: breakdown.sourceCount,
      explanation: `${Math.min(evidence.length, 5)}/5 sources (capped at 5)`,
    },
    {
      key: 'authority',
      label: 'Authority',
      weight: 0.30,
      value: breakdown.authority,
      explanation: 'Mean authority weight of source types',
    },
    {
      key: 'recency',
      label: 'Recency',
      weight: 0.25,
      value: breakdown.recency,
      explanation: 'Mean recency score across evidence',
    },
    {
      key: 'consistency',
      label: 'Consistency',
      weight: 0.15,
      value: breakdown.consistency,
      explanation: `${evidence.filter(e => e.supports_requirement).length}/${evidence.length} supporting`,
    },
  ]

  if (evidence.length === 0) {
    return (
      <div className="text-xs text-text-tertiary italic">No evidence to compute confidence.</div>
    )
  }

  return (
    <div className="mt-3">
      <h4 className="text-sm font-semibold mb-2">
        Confidence Breakdown <span className="font-normal text-text-tertiary">({breakdown.total.toFixed(2)})</span>
      </h4>

      {/* Stacked bar */}
      <div className="flex h-5 rounded-xs overflow-hidden mb-2">
        {segments.map(seg => {
          const widthPct = seg.weight * seg.value * 100 / Math.max(breakdown.total, 0.01) * breakdown.total
          return (
            <div
              key={seg.key}
              className={`${getSegmentColor(seg.value)} transition-all duration-200 relative cursor-pointer`}
              style={{ width: `${Math.max(widthPct, 2)}%` }}
              onMouseEnter={() => setHoveredSegment(seg.key)}
              onMouseLeave={() => setHoveredSegment(null)}
            >
              {/* Tooltip */}
              {hoveredSegment === seg.key && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 bg-text-primary text-white text-[10px] px-2 py-1 rounded-xs whitespace-nowrap z-10 shadow-md">
                  <strong>{seg.label}</strong> ({(seg.weight * 100).toFixed(0)}%): {seg.value.toFixed(2)}
                  <br />
                  {seg.explanation}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-[10px] text-text-tertiary">
        {segments.map(seg => (
          <span key={seg.key} className="inline-flex items-center gap-1">
            <span className={`w-2.5 h-2.5 rounded-full ${getSegmentColor(seg.value)}`} />
            {seg.label} ({(seg.weight * 100).toFixed(0)}%): {seg.value.toFixed(2)}
          </span>
        ))}
      </div>
    </div>
  )
}
