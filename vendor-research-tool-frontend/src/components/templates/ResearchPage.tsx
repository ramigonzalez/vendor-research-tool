import { useCallback, useState } from 'react'
import type { ResearchResults } from '../../lib/types'
import { apiFetch } from '../../lib/api'
import { useResearchState } from '../../hooks/useResearchState'
import { ComparisonMatrix } from '../organisms/ComparisonMatrix'
import { DrillDownPanel } from '../organisms/DrillDownPanel'
import { ExecutiveSummary } from '../organisms/ExecutiveSummary'
import { JobHistory } from '../organisms/JobHistory'
import { PipelineStepper } from '../organisms/PipelineStepper'
import { ScoringMethodology } from '../organisms/ScoringMethodology'
import { AuditView } from '../organisms/AuditView'
import { LiveCounters } from '../molecules/LiveCounters'
import { PriorityWeights } from '../molecules/PriorityWeights'
import { ThemeToggle } from '../atoms/ThemeToggle'

export function ResearchPage() {
  const { state, startResearch, setResults } = useResearchState()

  // Drill-down state
  const [drillDownOpen, setDrillDownOpen] = useState(false)
  const [drillDownVendor, setDrillDownVendor] = useState<string | null>(null)
  const [drillDownReqId, setDrillDownReqId] = useState<string | null>(null)

  // Track the job ID for historical audit event loading
  const [viewedJobId, setViewedJobId] = useState<string | null>(null)

  const loadResults = useCallback(async (jobId: string) => {
    try {
      const data = await apiFetch<ResearchResults>(`/api/research/${jobId}`)
      if ('matrix' in data) {
        setResults(data)
        setViewedJobId(jobId)
      }
    } catch {
      // Error loading results
    }
  }, [setResults])

  const openDrillDown = useCallback((vendor: string, reqId: string) => {
    setDrillDownVendor(vendor)
    setDrillDownReqId(reqId)
    setDrillDownOpen(true)
  }, [])

  const closeDrillDown = useCallback(() => {
    setDrillDownOpen(false)
  }, [])

  const isComplete = state.currentPhase === 'complete'
  const hasAuditData = state.activities.length > 0 || state.queries.length > 0
  const hasResults = !!state.results
  const showHero = !hasResults && !state.isRunning && !state.error

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      {/* Skip to content link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-accent-primary focus:text-white focus:px-4 focus:py-2 focus:rounded-sm"
      >
        Skip to content
      </a>

      <div id="main-content" className="mx-auto max-w-5xl px-6 py-5">
        {/* Header bar */}
        <header className="flex items-center justify-between border-b border-border-default pb-4 mb-6">
          <h1 className="text-2xl font-semibold text-text-primary m-0">
            SignalCore Vendor Research Tool
          </h1>
          <ThemeToggle />
        </header>

        {/* Hero empty state */}
        {showHero && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <h2 className="text-3xl font-heading font-semibold text-text-primary mb-3">
              Vendor Research, Automated
            </h2>
            <p className="text-text-secondary text-lg max-w-md mb-8">
              Compare vendors across your requirements with AI-powered research, scoring, and analysis.
            </p>
            <button
              onClick={startResearch}
              className="bg-accent-primary text-white border-none px-8 py-3.5 text-base rounded-sm cursor-pointer font-body-ui font-medium hover:bg-accent-primary-hover transition-colors"
            >
              Run Research
            </button>

            {/* Job History below hero */}
            <div className="w-full mt-12">
              <JobHistory onViewResults={loadResults} />
            </div>
          </div>
        )}

        {/* Inline controls when not in hero state */}
        {!showHero && (
          <>
            <div className="flex items-center gap-3 mb-6">
              <button
                onClick={startResearch}
                disabled={state.isRunning}
                className="bg-accent-primary text-white border-none px-6 py-2.5 text-sm rounded-sm cursor-pointer font-body-ui font-medium hover:bg-accent-primary-hover disabled:bg-text-tertiary disabled:cursor-not-allowed transition-colors"
              >
                {state.isRunning ? 'Running...' : 'New Research'}
              </button>
            </div>

            {/* Job History */}
            <JobHistory onViewResults={loadResults} />
          </>
        )}

        {/* Pipeline Visualization (during research) */}
        {state.isRunning && (
          <div className="space-y-6 mt-6">
            <PipelineStepper
              stepStatuses={state.stepStatuses}
              elapsedTime={state.elapsedTime}
            />

            <LiveCounters
              sourceCount={state.sourceCount}
              elapsedTime={state.elapsedTime}
              isComplete={false}
            />

            <AuditView
              stepStatuses={state.stepStatuses}
              sources={state.sources}
              sourceCount={state.sourceCount}
              queries={state.queries}
              activities={state.activities}
              currentIteration={state.currentIteration}
              isComplete={false}
              hasAuditData={hasAuditData}
              jobId={state.jobId}
            />
          </div>
        )}

        {/* Error Section */}
        {state.error && (
          <div className="my-5 p-5 bg-red-50 border border-status-error rounded-sm">
            <div className="text-status-error font-medium">Error: {state.error}</div>
            <button
              onClick={startResearch}
              className="bg-status-error text-white border-none px-4 py-2 rounded-xs cursor-pointer mt-2.5 text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* Results */}
        {hasResults && (
          <div className="space-y-6 mt-6">
            {/* Completed counters */}
            {isComplete && (
              <LiveCounters
                sourceCount={state.sourceCount}
                elapsedTime={state.elapsedTime}
                isComplete={true}
              />
            )}

            {/* Audit View (post-research — live data or historical fetch) */}
            <AuditView
              stepStatuses={state.stepStatuses}
              sources={state.sources}
              sourceCount={state.sourceCount}
              queries={state.queries}
              activities={state.activities}
              currentIteration={state.currentIteration}
              isComplete={true}
              hasAuditData={hasAuditData}
              jobId={state.jobId ?? viewedJobId}
            />

            <ExecutiveSummary results={state.results!} />

            <ScoringMethodology />

            <ComparisonMatrix results={state.results!} onCellClick={openDrillDown} />

            <PriorityWeights results={state.results!} />
          </div>
        )}

        {/* Drill-down Panel */}
        <DrillDownPanel
          isOpen={drillDownOpen}
          vendor={drillDownVendor}
          requirementId={drillDownReqId}
          results={state.results}
          onClose={closeDrillDown}
        />
      </div>
    </div>
  )
}
