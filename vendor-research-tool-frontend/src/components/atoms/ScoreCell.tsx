import type { ScoreStatus } from '../../lib/types'

interface ScoreCellProps {
  score: number
  confidence: number
  status?: ScoreStatus
  statusDetail?: string | null
  vendor: string
  requirementId: string
  requirementDesc: string
  onClick: (vendor: string, reqId: string) => void
}

function getScoreBarColor(score: number): string {
  if (score >= 7) return 'bg-confidence-high'
  if (score >= 4) return 'bg-confidence-medium'
  return 'bg-confidence-low'
}

function getConfidenceTextColor(confidence: number): string {
  if (confidence >= 0.7) return 'text-confidence-high'
  if (confidence >= 0.4) return 'text-confidence-medium'
  return 'text-confidence-low'
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`
}

export function ScoreCell({ score, confidence, status, statusDetail, vendor, requirementId, requirementDesc, onClick }: ScoreCellProps) {
  const effectiveStatus = status ?? (confidence > 0 ? 'ok' : 'degraded')
  const isOk = effectiveStatus === 'ok'
  const barColor = getScoreBarColor(score)
  const confColor = getConfidenceTextColor(confidence)
  const warnIcon = confidence < 0.4 ? ' \u26A0' : ''
  const barWidth = (score / 10) * 100

  return (
    <td
      role="button"
      tabIndex={0}
      title={statusDetail ?? undefined}
      aria-label={isOk
        ? `${vendor} ${requirementDesc}: score ${score.toFixed(1)} out of 10, confidence ${formatConfidence(confidence)}`
        : `${vendor} ${requirementDesc}: ${statusDetail ?? effectiveStatus}`
      }
      className={`bg-bg-primary cursor-pointer text-sm text-center px-3 py-2.5 border border-border-default hover:bg-accent-primary/5 transition-colors focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:outline-none`}
      onClick={() => onClick(vendor, requirementId)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick(vendor, requirementId)
        }
      }}
    >
      {isOk ? (
        <>
          <span className="block font-bold text-text-primary">{score.toFixed(1)}</span>
          <div className="h-1.5 mt-1 bg-border-default rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${barColor}`}
              style={{ width: `${barWidth}%` }}
            />
          </div>
          <span className={`block text-[10px] font-medium mt-1 ${confColor}`}>
            {formatConfidence(confidence)}{warnIcon}
          </span>
        </>
      ) : effectiveStatus === 'error' ? (
        <span className="block text-xs text-status-error" title={statusDetail ?? undefined}>
          {'\u26A0'} Error
        </span>
      ) : (
        <span className="block text-xs text-text-tertiary italic">No evidence</span>
      )}
    </td>
  )
}

export function EmptyScoreCell() {
  return (
    <td className="bg-bg-primary text-text-tertiary text-sm text-center px-3 py-2.5 border border-border-default hover:bg-accent-primary/5 transition-colors">
      &mdash;
    </td>
  )
}
