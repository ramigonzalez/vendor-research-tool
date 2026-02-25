import { useState } from 'react'
import type { ActivityEntry, QueryInfo, SourceInfo } from '../../hooks/useResearchState'
import type { StepStatus } from '../../lib/types'
import { ActivityFeed } from './ActivityFeed'
import { QueryHistory } from './QueryHistory'
import { ResearchTimeline } from './ResearchTimeline'
import { SourcesVisited } from './SourcesVisited'

interface AuditViewProps {
  stepStatuses: Record<string, StepStatus>
  sources: SourceInfo[]
  sourceCount: number
  queries: QueryInfo[]
  activities: ActivityEntry[]
  currentIteration: number
  isComplete: boolean
  hasAuditData: boolean
}

const tabs = [
  { key: 'timeline', label: 'Timeline' },
  { key: 'queries', label: 'Queries' },
  { key: 'sources', label: 'Sources' },
  { key: 'activity', label: 'Activity Log' },
] as const

type TabKey = typeof tabs[number]['key']

export function AuditView({
  stepStatuses,
  sources,
  sourceCount,
  queries,
  activities,
  currentIteration,
  isComplete,
  hasAuditData,
}: AuditViewProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('timeline')

  if (!hasAuditData && isComplete) {
    return (
      <div className="my-4 p-4 bg-bg-secondary rounded-sm text-sm text-text-tertiary italic">
        Audit trail not available for this run.
      </div>
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const currentIndex = tabs.findIndex(t => t.key === activeTab)
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      const next = (currentIndex + 1) % tabs.length
      setActiveTab(tabs[next].key)
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      const prev = (currentIndex - 1 + tabs.length) % tabs.length
      setActiveTab(tabs[prev].key)
    }
  }

  return (
    <div className="my-4 bg-bg-secondary rounded-sm border border-border-subtle overflow-hidden">
      {/* Tab bar */}
      <div role="tablist" className="flex border-b border-border-default" onKeyDown={handleKeyDown}>
        {tabs.map(tab => {
          const isActive = activeTab === tab.key
          let count = ''
          if (tab.key === 'queries') count = ` (${queries.length})`
          if (tab.key === 'sources') count = ` (${sourceCount})`
          if (tab.key === 'activity') count = ` (${activities.length})`

          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${tab.key}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm cursor-pointer border-none bg-transparent transition-colors
                ${isActive
                  ? 'text-accent-primary border-b-2 border-b-accent-primary font-medium'
                  : 'text-text-secondary hover:text-text-primary'
                }
                focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:outline-none
              `}
            >
              {tab.label}{count}
            </button>
          )
        })}
      </div>

      {/* Tab panels */}
      <div
        role="tabpanel"
        id={`tabpanel-${activeTab}`}
        aria-labelledby={activeTab}
      >
        {activeTab === 'timeline' && (
          <ResearchTimeline
            stepStatuses={stepStatuses}
            sources={sources}
            sourceCount={sourceCount}
            currentIteration={currentIteration}
            isComplete={isComplete}
          />
        )}
        {activeTab === 'queries' && <QueryHistory queries={queries} />}
        {activeTab === 'sources' && <SourcesVisited sources={sources} />}
        {activeTab === 'activity' && <ActivityFeed activities={activities} />}
      </div>
    </div>
  )
}
