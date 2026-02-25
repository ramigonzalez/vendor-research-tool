import { useEffect, useRef } from 'react'
import type { ResearchResults, ScoreResult } from '../../lib/types'
import { ConfidenceBreakdown } from '../molecules/ConfidenceBreakdown'
import { ScoreBreakdown } from '../molecules/ScoreBreakdown'

interface DrillDownPanelProps {
  isOpen: boolean
  vendor: string | null
  requirementId: string | null
  results: ResearchResults | null
  onClose: () => void
}

const BADGE_COLORS: Record<string, string> = {
  official_docs: 'bg-accent-tertiary',
  github: 'bg-text-primary',
  comparison: 'bg-status-analyzing',
  blog: 'bg-confidence-medium',
  community: 'bg-text-tertiary',
}

export function DrillDownPanel({ isOpen, vendor, requirementId, results, onClose }: DrillDownPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  // Focus trap and return-focus
  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement
      panelRef.current?.focus()
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus()
    }
  }, [isOpen])

  // Escape key handler
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKey)
      return () => document.removeEventListener('keydown', handleKey)
    }
  }, [isOpen, onClose])

  if (!isOpen || !vendor || !requirementId || !results) return null

  const scoreResult: ScoreResult | undefined = results.matrix[vendor]?.[requirementId]
  if (!scoreResult) return null

  const req = results.requirements.find(r => r.id === requirementId)
  const reqName = req?.description ?? requirementId
  const evidence = [...(scoreResult.evidence || [])].sort((a, b) => (b.relevance || 0) - (a.relevance || 0))

  return (
    <div className={`fixed inset-0 z-[999]`}>
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      {/* Panel */}
      <div
        ref={panelRef}
        role="dialog"
        aria-labelledby="drill-down-title"
        tabIndex={-1}
        className={`fixed right-0 top-0 bottom-0 w-[440px] max-w-[90vw] bg-bg-secondary overflow-y-auto p-6 z-[1000] shadow-lg transition-transform duration-200 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        } focus-visible:outline-none`}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-4 text-xl text-text-secondary hover:text-text-primary bg-transparent border-none cursor-pointer focus-visible:ring-2 focus-visible:ring-accent-primary rounded"
          aria-label="Close panel"
        >
          &times;
        </button>

        {/* Header */}
        <div id="drill-down-title" className="mb-4 border-b border-border-default pb-3">
          <h3 className="text-lg font-semibold text-text-primary m-0 mb-1">
            {vendor} &mdash; {reqName}
          </h3>
          <div className="text-sm text-text-secondary">
            Score: <strong>{scoreResult.score.toFixed(1)}</strong>/10 &nbsp;|&nbsp;
            Confidence: <strong>{scoreResult.confidence.toFixed(2)}</strong>
          </div>
        </div>

        {/* Justification */}
        {scoreResult.justification && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold mb-1">Justification</h4>
            <p className="text-sm leading-relaxed text-text-secondary">{scoreResult.justification}</p>
          </div>
        )}

        {/* Limitations */}
        {scoreResult.limitations.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold mb-1">Limitations</h4>
            <ul className="pl-5 text-sm text-text-secondary">
              {scoreResult.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Score Breakdown (Story 10.3) */}
        <ScoreBreakdown scoreResult={scoreResult} />

        {/* Confidence Breakdown (Story 10.2) */}
        <ConfidenceBreakdown evidence={scoreResult.evidence} />

        {/* Evidence */}
        <div className="mt-4">
          <h4 className="text-sm font-semibold mb-2">Evidence ({evidence.length})</h4>
          {evidence.length === 0 ? (
            <p className="text-text-tertiary text-sm italic">No evidence collected for this pair.</p>
          ) : (
            evidence.map((e, i) => {
              const claim = e.claim.length > 300 ? e.claim.slice(0, 300) + '...' : e.claim
              const badgeColor = BADGE_COLORS[e.source_type] || 'bg-text-tertiary'
              return (
                <div key={i} className="mb-3.5 p-2.5 bg-bg-primary rounded-sm border-l-[3px] border-border-default">
                  <div className="text-sm text-text-primary mb-1.5">{claim}</div>
                  <span className={`inline-block px-1.5 py-0.5 rounded text-xs text-white mr-1.5 ${badgeColor}`}>
                    {e.source_type}
                  </span>
                  <a
                    href={e.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-text-link hover:underline"
                  >
                    {e.source_name || 'Source'}
                  </a>
                  <div className="text-xs text-text-tertiary mt-1">
                    Relevance: {(e.relevance || 0).toFixed(2)}
                    {e.content_date && ` | ${e.content_date}`}
                    {' | '}
                    {e.supports_requirement ? (
                      <span className="text-confidence-high">&#10003; Supports</span>
                    ) : (
                      <span className="text-confidence-low">&#10007; Does not support</span>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
