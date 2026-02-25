import { useEffect, useState } from 'react'
import type { ActivityEntry, QueryInfo, SourceInfo } from '../../hooks/useResearchState'
import { apiFetch } from '../../lib/api'
import type { AuditEvent, StepStatus } from '../../lib/types'
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
  /** Job ID for fetching historical audit events */
  jobId?: string | null
}

const tabs = [
  { key: 'timeline', label: 'Timeline' },
  { key: 'queries', label: 'Queries' },
  { key: 'sources', label: 'Sources' },
  { key: 'activity', label: 'Activity Log' },
] as const

type TabKey = typeof tabs[number]['key']

/** Map persisted audit events into the shape the sub-components expect */
function hydrateFromAuditEvents(events: AuditEvent[]) {
  const sources: SourceInfo[] = []
  const queries: QueryInfo[] = []
  const activities: ActivityEntry[] = []
  const stepStatuses: Record<string, StepStatus> = {
    planning: 'pending', searching: 'pending', analyzing: 'pending',
    scoring: 'pending', ranking: 'pending', writing: 'pending', complete: 'pending',
  }
  let iteration = 0
  let id = 0

  const eventStart = events.length > 0 ? new Date(events[0].created_at).getTime() : 0

  for (const evt of events) {
    const p = evt.payload
    const ts = new Date(evt.created_at).getTime() - eventStart

    switch (evt.event_type) {
      case 'phase_start':
        if (typeof p.phase === 'string') stepStatuses[p.phase] = 'active'
        activities.push({ id: ++id, timestamp: ts, icon: '\u25B6', message: `Phase started: ${p.phase}`, variant: 'default', eventType: 'phase_start' })
        break
      case 'phase_end':
        if (typeof p.phase === 'string') stepStatuses[p.phase] = 'complete'
        break
      case 'query_generated':
        queries.push({
          vendor: p.vendor as string,
          requirementId: p.requirement_id as string,
          queries: p.queries as string[],
          isRefined: iteration > 0,
        })
        activities.push({ id: ++id, timestamp: ts, icon: '\uD83D\uDD0D', message: `Generated queries for ${p.vendor} \u00D7 ${p.requirement_id}`, variant: 'default', eventType: 'query_generated' })
        break
      case 'search_result':
        sources.push({
          url: p.source_url as string,
          name: p.source_name as string,
          domain: p.domain as string,
          vendor: p.vendor as string,
          requirementId: p.requirement_id as string,
        })
        break
      case 'evidence_extracted':
        activities.push({ id: ++id, timestamp: ts, icon: '\uD83D\uDCCB', message: `Extracted ${p.count} evidence items for ${p.vendor} \u00D7 ${p.requirement_id}`, variant: 'default', eventType: 'evidence_extracted' })
        break
      case 'score_computed':
        activities.push({ id: ++id, timestamp: ts, icon: '\uD83D\uDCCA', message: `Scored: ${p.vendor} ${p.requirement_id} = ${(p.score as number).toFixed(1)} (conf: ${(p.confidence as number).toFixed(2)})`, variant: 'default', eventType: 'score_computed' })
        break
      case 'vendor_ranked':
        activities.push({ id: ++id, timestamp: ts, icon: '\uD83C\uDFC6', message: `Ranked: #${p.rank} ${p.vendor} (${(p.overall_score as number).toFixed(1)})`, variant: 'default', eventType: 'vendor_ranked' })
        break
      case 'warning':
        activities.push({ id: ++id, timestamp: ts, icon: '\u26A0\uFE0F', message: p.message as string, variant: 'warning', eventType: 'warning' })
        break
      case 'iteration_start':
        iteration = p.iteration as number
        activities.push({ id: ++id, timestamp: ts, icon: '\uD83D\uDD04', message: `Gap-fill round ${p.iteration}: searching ${p.total_searches} refined queries for ${p.gap_count} evidence gaps`, variant: 'default', eventType: 'iteration_start' })
        break
      case 'completed':
        stepStatuses.complete = 'complete'
        activities.push({ id: ++id, timestamp: ts, icon: '\u2705', message: 'Research complete', variant: 'default', eventType: 'completed' })
        break
      case 'started':
        activities.push({ id: ++id, timestamp: ts, icon: '\uD83D\uDE80', message: `Research started`, variant: 'default', eventType: 'started' })
        break
    }
  }

  return { sources, queries, activities: activities.reverse(), stepStatuses, sourceCount: sources.length, iteration }
}

export function AuditView({
  stepStatuses: liveStepStatuses,
  sources: liveSources,
  sourceCount: liveSourceCount,
  queries: liveQueries,
  activities: liveActivities,
  currentIteration: liveIteration,
  isComplete,
  hasAuditData,
  jobId,
}: AuditViewProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('timeline')
  const [historicalData, setHistoricalData] = useState<ReturnType<typeof hydrateFromAuditEvents> | null>(null)
  const shouldFetch = !hasAuditData && isComplete && !!jobId
  const [loading, setLoading] = useState(shouldFetch)
  const [isCollapsed, setIsCollapsed] = useState(isComplete)

  // Collapse when isComplete transitions to true (React "store previous props" pattern)
  const [prevIsComplete, setPrevIsComplete] = useState(isComplete)
  if (isComplete && !prevIsComplete) {
    setPrevIsComplete(true)
    setIsCollapsed(true)
  }

  // Fetch historical audit events when viewing a completed job without live data
  useEffect(() => {
    if (!shouldFetch) return
    apiFetch<AuditEvent[]>(`/api/research/${jobId!}/audit`)
      .then(events => {
        if (events.length > 0) {
          setHistoricalData(hydrateFromAuditEvents(events))
        }
      })
      .catch(() => { /* Audit data unavailable */ })
      .finally(() => setLoading(false))
  }, [shouldFetch, jobId])

  // Use historical data if available, otherwise use live data
  const stepStatuses = historicalData?.stepStatuses ?? liveStepStatuses
  const sources = historicalData?.sources ?? liveSources
  const sourceCount = historicalData?.sourceCount ?? liveSourceCount
  const queries = historicalData?.queries ?? liveQueries
  const activities = historicalData?.activities ?? liveActivities
  const currentIteration = historicalData?.iteration ?? liveIteration
  const hasData = hasAuditData || historicalData !== null

  if (loading) {
    return (
      <div className="p-4 bg-bg-secondary rounded-sm text-sm text-text-tertiary italic">
        Loading audit trail...
      </div>
    )
  }

  if (!hasData && isComplete) {
    return (
      <div className="p-4 bg-bg-secondary rounded-sm text-sm text-text-tertiary italic">
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

  // Summary text for the disclosure header
  const summaryParts: string[] = []
  if (sourceCount > 0) summaryParts.push(`${sourceCount} sources`)
  if (queries.length > 0) summaryParts.push(`${queries.length} queries`)
  const summaryText = summaryParts.length > 0 ? ` \u2014 ${summaryParts.join(', ')}` : ''

  return (
    <div className="bg-bg-secondary rounded-sm border border-border-subtle overflow-hidden">
      {/* Disclosure header */}
      {isComplete ? (
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-expanded={!isCollapsed}
          className="w-full text-left px-4 py-3 bg-bg-secondary hover:bg-bg-primary transition-colors text-sm font-medium text-text-primary flex items-center justify-between cursor-pointer border-none"
        >
          <span>
            Research Analysis{summaryText}
          </span>
          <span className={`text-text-tertiary transition-transform duration-fast ${isCollapsed ? '' : 'rotate-180'}`}>
            {'\u25BC'}
          </span>
        </button>
      ) : (
        <div className="px-4 py-3 text-sm font-medium text-text-primary border-b border-border-default">
          Research Analysis{summaryText}
        </div>
      )}

      {/* Collapsible content */}
      <div
        className={`transition-all duration-normal ease-smooth overflow-hidden ${
          isComplete && isCollapsed ? 'max-h-0 opacity-0' : 'max-h-[2000px] opacity-100'
        }`}
      >
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
    </div>
  )
}
