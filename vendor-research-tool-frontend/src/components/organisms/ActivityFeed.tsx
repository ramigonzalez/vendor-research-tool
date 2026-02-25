import { useEffect, useRef, useState } from 'react'
import type { ActivityEntry } from '../../hooks/useResearchState'

interface ActivityFeedProps {
  activities: ActivityEntry[]
  isCollapsed?: boolean
}

function formatRelativeTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return `+${m}:${s.toString().padStart(2, '0')}`
}

export function ActivityFeed({ activities, isCollapsed: initialCollapsed }: ActivityFeedProps) {
  const [isCollapsed, setIsCollapsed] = useState(initialCollapsed ?? false)
  const containerRef = useRef<HTMLDivElement>(null)
  const userScrolledRef = useRef(false)

  // Auto-scroll unless user has scrolled up
  useEffect(() => {
    const container = containerRef.current
    if (!container || userScrolledRef.current) return
    container.scrollTop = 0 // New entries at top
  }, [activities])

  const handleScroll = () => {
    const container = containerRef.current
    if (!container) return
    userScrolledRef.current = container.scrollTop > 20
  }

  // Show max 100 DOM entries
  const displayActivities = activities.slice(0, 100)

  return (
    <div className="my-4">
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="text-sm text-text-secondary hover:text-text-primary mb-2 cursor-pointer bg-transparent border-none flex items-center gap-1"
      >
        <span>{isCollapsed ? '\u25B6' : '\u25BC'}</span>
        Activity Log ({activities.length})
      </button>

      {!isCollapsed && (
        <div
          ref={containerRef}
          onScroll={handleScroll}
          className="max-h-[300px] overflow-y-auto bg-bg-secondary rounded-sm border border-border-subtle"
          role="log"
          aria-live="polite"
        >
          {displayActivities.length === 0 ? (
            <p className="p-3 text-xs text-text-tertiary italic">No activity yet.</p>
          ) : (
            displayActivities.map(entry => (
              <div
                key={entry.id}
                className={`flex items-start gap-2 px-3 py-1.5 border-b border-border-subtle last:border-b-0 text-xs animate-token-fade-in
                  ${entry.variant === 'warning' ? 'bg-status-warning/10 border-l-2 border-l-status-warning' : ''}
                `}
              >
                <span className="text-text-tertiary font-mono whitespace-nowrap w-12">
                  {formatRelativeTime(entry.timestamp)}
                </span>
                <span className="flex-shrink-0">{entry.icon}</span>
                <span className={`flex-1 ${entry.variant === 'warning' ? 'text-status-warning' : 'text-text-secondary'}`}>
                  {entry.message}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
