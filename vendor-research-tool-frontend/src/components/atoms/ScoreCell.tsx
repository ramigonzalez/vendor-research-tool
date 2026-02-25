interface ScoreCellProps {
  score: number
  confidence: number
  vendor: string
  requirementId: string
  requirementDesc: string
  onClick: (vendor: string, reqId: string) => void
}

function getScoreColorClass(score: number): string {
  if (score >= 7) return 'bg-confidence-high'
  if (score >= 4) return 'bg-confidence-medium'
  return 'bg-confidence-low'
}

function getConfidenceClass(confidence: number): string {
  if (confidence >= 0.7) return 'border-2 border-transparent'
  if (confidence >= 0.4) return 'border-2 border-dashed border-text-tertiary opacity-80'
  return 'border-2 border-dashed border-confidence-low opacity-60'
}

export function ScoreCell({ score, confidence, vendor, requirementId, requirementDesc, onClick }: ScoreCellProps) {
  const colorClass = getScoreColorClass(score)
  const confClass = getConfidenceClass(confidence)
  const warnIcon = confidence < 0.4 ? ' \u26A0' : ''

  return (
    <td
      role="button"
      tabIndex={0}
      aria-label={`${vendor} ${requirementDesc}: score ${score.toFixed(1)}, confidence ${confidence.toFixed(2)}`}
      className={`${colorClass} ${confClass} cursor-pointer text-white font-bold text-sm text-center px-3 py-2 rounded-xs hover:brightness-110 transition-all focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:outline-none`}
      onClick={() => onClick(vendor, requirementId)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick(vendor, requirementId)
        }
      }}
    >
      <span className="block">{score.toFixed(1)}{warnIcon}</span>
      <span className="block text-[10px] text-white/80 mt-0.5">conf: {confidence.toFixed(2)}</span>
    </td>
  )
}

export function EmptyScoreCell() {
  return (
    <td className="bg-text-tertiary text-white font-bold text-sm text-center px-3 py-2 rounded-xs">
      &mdash;
    </td>
  )
}
