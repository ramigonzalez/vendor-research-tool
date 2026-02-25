interface LiveCountersProps {
  sourceCount: number
  elapsedTime: number
  isComplete: boolean
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export function LiveCounters({ sourceCount, elapsedTime, isComplete }: LiveCountersProps) {
  return (
    <div className="flex gap-6 text-sm text-text-secondary" aria-atomic="true" aria-live="polite">
      <div className="flex items-center gap-1.5">
        <span className="text-base">{'\u{1F310}'}</span>
        <span>
          <strong className="text-text-primary">{sourceCount}</strong> sources {isComplete ? 'found' : 'found...'}
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-base">{'\u23F1\uFE0F'}</span>
        <span className="font-mono">{formatTime(elapsedTime)}</span>
      </div>
    </div>
  )
}
