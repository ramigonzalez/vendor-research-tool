import { useState } from 'react'
import type { StepStatus } from '../../lib/types'
import type { SourceInfo } from '../../hooks/useResearchState'
import { SourcePill } from '../molecules/SourcePill'

interface ResearchTimelineProps {
  stepStatuses: Record<string, StepStatus>
  sources: SourceInfo[]
  sourceCount: number
  currentIteration: number
  isComplete: boolean
}

const timelinePhases = [
  { key: 'planning', label: 'Planning queries', icon: '\u{1F4DD}' },
  { key: 'searching', label: 'Searching sources', icon: '\u{1F50D}' },
  { key: 'analyzing', label: 'Analyzing evidence', icon: '\u{1F9E0}' },
  { key: 'scoring', label: 'Computing scores', icon: '\u{1F4CA}' },
  { key: 'ranking', label: 'Ranking vendors', icon: '\u{1F3C6}' },
  { key: 'writing', label: 'Writing summary', icon: '\u{270D}\uFE0F' },
] as const

export function ResearchTimeline({ stepStatuses, sources, sourceCount, currentIteration, isComplete }: ResearchTimelineProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Auto-collapse after completion with delay
  const shouldCollapse = isComplete && isCollapsed

  // Deduplicate sources by domain for display
  const uniqueDomains = new Map<string, SourceInfo>()
  for (const source of sources) {
    if (!uniqueDomains.has(source.domain)) {
      uniqueDomains.set(source.domain, source)
    }
  }
  const displaySources = Array.from(uniqueDomains.values()).slice(0, 24)

  return (
    <div role="log" aria-live="polite" className="my-4 bg-bg-timeline rounded-sm p-4 border border-border-subtle">
      {/* Collapse toggle for completed state */}
      {isComplete && (
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-xs text-text-tertiary hover:text-text-secondary mb-2 cursor-pointer bg-transparent border-none"
        >
          {isCollapsed ? `\u25BC Show timeline (${sourceCount} sources found)` : '\u25B2 Collapse timeline'}
        </button>
      )}

      {!shouldCollapse && (
        <div className="space-y-3">
          {timelinePhases.map(phase => {
            const status = stepStatuses[phase.key] || 'pending'
            if (status === 'pending') return null

            return (
              <div key={phase.key} className="flex gap-3">
                {/* Timeline dot + line */}
                <div className="flex flex-col items-center">
                  <div className={`text-base ${status === 'active' ? 'animate-step-pulse' : ''}`}>
                    {status === 'complete' ? '\u2713' : phase.icon}
                  </div>
                  <div className="w-px flex-1 bg-border-default" />
                </div>

                {/* Content */}
                <div className="flex-1 pb-2">
                  <div className={`text-sm ${status === 'active' ? 'font-medium text-text-primary' : 'text-text-secondary'}`}>
                    {phase.label}
                    {phase.key === 'searching' && currentIteration > 1 && (
                      <span className="text-xs text-text-tertiary ml-2">
                        (Gap-fill round {currentIteration})
                      </span>
                    )}
                    {phase.key === 'searching' && status === 'active' && (
                      <span className="text-xs text-text-tertiary ml-2">
                        {sourceCount} sources found...
                      </span>
                    )}
                  </div>

                  {/* Source pills during searching */}
                  {phase.key === 'searching' && displaySources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {displaySources.map((s, i) => (
                        <SourcePill key={`${s.domain}-${i}`} domain={s.domain} name={s.name} url={s.url} />
                      ))}
                      {sourceCount > displaySources.length && (
                        <span className="inline-flex items-center px-2.5 py-1 text-xs text-text-tertiary">
                          +{sourceCount - displaySources.length} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Shimmer effect during analyzing */}
                  {phase.key === 'analyzing' && status === 'active' && (
                    <div className="h-2 mt-2 rounded-xs bg-gradient-to-r from-status-analyzing/20 via-status-analyzing/40 to-status-analyzing/20 bg-[length:200%_100%] animate-shimmer" />
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
