import { useCallback, useRef, useState } from 'react'
import type {
  ResearchPhase,
  ResearchResults,
  SSEEvent,
  SSESearchResultEvent,
  SSEQueryGeneratedEvent,
  StepStatus,
} from '../lib/types'
import { connectSSE } from '../lib/sse-client'

export interface SourceInfo {
  url: string
  name: string
  domain: string
  vendor: string
  requirementId: string
}

export interface QueryInfo {
  vendor: string
  requirementId: string
  queries: string[]
  isRefined: boolean
}

export interface ActivityEntry {
  id: number
  timestamp: number
  icon: string
  message: string
  variant: 'default' | 'warning'
  eventType: string
}

export interface ResearchState {
  currentPhase: ResearchPhase
  stepStatuses: Record<string, StepStatus>
  sources: SourceInfo[]
  queries: QueryInfo[]
  evidenceCounts: Record<string, number>
  scores: Record<string, { score: number; confidence: number }>
  rankings: { vendor: string; rank: number; overall_score: number }[]
  sourceCount: number
  elapsedTime: number
  results: ResearchResults | null
  error: string | null
  isRunning: boolean
  jobId: string | null
  activities: ActivityEntry[]
  currentIteration: number
}

const PIPELINE_STEPS = ['planning', 'searching', 'analyzing', 'scoring', 'ranking', 'writing', 'complete'] as const

function initialStepStatuses(): Record<string, StepStatus> {
  const statuses: Record<string, StepStatus> = {}
  for (const step of PIPELINE_STEPS) {
    statuses[step] = 'pending'
  }
  return statuses
}

function initialState(): ResearchState {
  return {
    currentPhase: 'idle',
    stepStatuses: initialStepStatuses(),
    sources: [],
    queries: [],
    evidenceCounts: {},
    scores: {},
    rankings: [],
    sourceCount: 0,
    elapsedTime: 0,
    results: null,
    error: null,
    isRunning: false,
    jobId: null,
    activities: [],
    currentIteration: 0,
  }
}

export function useResearchState() {
  const [state, setState] = useState<ResearchState>(initialState)
  const abortRef = useRef<AbortController | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startTimeRef = useRef<number>(0)
  const activityIdRef = useRef(0)

  const addActivity = useCallback((icon: string, message: string, variant: 'default' | 'warning', eventType: string) => {
    const entry: ActivityEntry = {
      id: ++activityIdRef.current,
      timestamp: Date.now() - startTimeRef.current,
      icon,
      message,
      variant,
      eventType,
    }
    setState(prev => ({
      ...prev,
      activities: [entry, ...prev.activities].slice(0, 200),
    }))
  }, [])

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case 'started':
        setState(prev => ({ ...prev, jobId: event.job_id }))
        addActivity('\u{1F680}', `Research started (Job: ${event.job_id.slice(0, 8)}...)`, 'default', 'started')
        break

      case 'progress':
        // Legacy progress events — update phase if present
        if (event.phase) {
          setState(prev => ({ ...prev, currentPhase: event.phase as ResearchPhase }))
        }
        break

      case 'phase_start':
        setState(prev => {
          const newStatuses = { ...prev.stepStatuses }
          newStatuses[event.phase] = 'active'
          return { ...prev, currentPhase: event.phase as ResearchPhase, stepStatuses: newStatuses }
        })
        addActivity('\u{25B6}', `Phase started: ${event.phase}`, 'default', 'phase_start')
        break

      case 'phase_end':
        setState(prev => {
          const newStatuses = { ...prev.stepStatuses }
          newStatuses[event.phase] = 'complete'
          return { ...prev, stepStatuses: newStatuses }
        })
        break

      case 'query_generated': {
        const qe = event as SSEQueryGeneratedEvent
        setState(prev => ({
          ...prev,
          queries: [...prev.queries, {
            vendor: qe.vendor,
            requirementId: qe.requirement_id,
            queries: qe.queries,
            isRefined: prev.currentIteration > 0,
          }],
        }))
        addActivity('\u{1F50D}', `Generated queries for ${qe.vendor} \u00D7 ${qe.requirement_id}`, 'default', 'query_generated')
        break
      }

      case 'search_result': {
        const sr = event as SSESearchResultEvent
        const source: SourceInfo = {
          url: sr.source_url,
          name: sr.source_name,
          domain: sr.domain,
          vendor: sr.vendor,
          requirementId: sr.requirement_id,
        }
        setState(prev => ({
          ...prev,
          sources: [...prev.sources, source],
          sourceCount: prev.sourceCount + 1,
        }))
        break
      }

      case 'evidence_extracted':
        setState(prev => ({
          ...prev,
          evidenceCounts: {
            ...prev.evidenceCounts,
            [`${event.vendor}:${event.requirement_id}`]: event.count,
          },
        }))
        addActivity('\u{1F4CB}', `Extracted ${event.count} evidence items for ${event.vendor} \u00D7 ${event.requirement_id}`, 'default', 'evidence_extracted')
        break

      case 'score_computed':
        setState(prev => ({
          ...prev,
          scores: {
            ...prev.scores,
            [`${event.vendor}:${event.requirement_id}`]: {
              score: event.score,
              confidence: event.confidence,
            },
          },
        }))
        addActivity('\u{1F4CA}', `Scored: ${event.vendor} ${event.requirement_id} = ${event.score.toFixed(1)} (conf: ${event.confidence.toFixed(2)})`, 'default', 'score_computed')
        break

      case 'vendor_ranked':
        setState(prev => ({
          ...prev,
          rankings: [...prev.rankings.filter(r => r.vendor !== event.vendor), {
            vendor: event.vendor,
            rank: event.rank,
            overall_score: event.overall_score,
          }],
        }))
        addActivity('\u{1F3C6}', `Ranked: #${event.rank} ${event.vendor} (${event.overall_score.toFixed(1)})`, 'default', 'vendor_ranked')
        break

      case 'warning':
        addActivity('\u26A0\uFE0F', `${event.message}`, 'warning', 'warning')
        break

      case 'iteration_start':
        setState(prev => ({ ...prev, currentIteration: event.iteration }))
        addActivity('\u{1F504}', `Gap-fill round ${event.iteration}: searching ${event.total_searches} refined queries for ${event.gap_count} evidence gaps`, 'default', 'iteration_start')
        break

      case 'completed':
        setState(prev => ({
          ...prev,
          currentPhase: 'complete',
          stepStatuses: { ...prev.stepStatuses, complete: 'complete' },
          results: event.results,
          isRunning: false,
        }))
        if (timerRef.current) {
          clearInterval(timerRef.current)
          timerRef.current = null
        }
        addActivity('\u2705', 'Research complete', 'default', 'completed')
        break

      case 'error':
        setState(prev => ({
          ...prev,
          currentPhase: 'error',
          error: event.message,
          isRunning: false,
        }))
        if (timerRef.current) {
          clearInterval(timerRef.current)
          timerRef.current = null
        }
        addActivity('\u274C', `Error: ${event.message}`, 'warning', 'error')
        break
    }
  }, [addActivity])

  const startResearch = useCallback(() => {
    // Reset state
    setState({ ...initialState(), isRunning: true })
    startTimeRef.current = Date.now()
    activityIdRef.current = 0

    // Start timer
    timerRef.current = setInterval(() => {
      setState(prev => ({
        ...prev,
        elapsedTime: Math.floor((Date.now() - startTimeRef.current) / 1000),
      }))
    }, 1000)

    // Connect SSE
    abortRef.current = connectSSE(handleEvent)
  }, [handleEvent])

  const cancelResearch = useCallback(() => {
    abortRef.current?.abort()
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setState(prev => ({ ...prev, isRunning: false, currentPhase: 'idle' }))
  }, [])

  return {
    state,
    startResearch,
    cancelResearch,
    setResults: (results: ResearchResults) => setState(prev => ({ ...prev, results })),
  }
}
