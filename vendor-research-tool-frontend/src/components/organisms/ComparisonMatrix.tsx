import type { Requirement, ResearchResults, VendorRanking } from '../../lib/types'
import { Badge } from '../atoms/Badge'
import { EmptyScoreCell, ScoreCell } from '../atoms/ScoreCell'

interface ComparisonMatrixProps {
  results: ResearchResults
  onCellClick: (vendor: string, reqId: string) => void
}

const priorityOrder = ['high', 'medium', 'low'] as const
const priorityLabels: Record<string, string> = {
  high: 'High Priority',
  medium: 'Medium Priority',
  low: 'Low Priority',
}
const prioritySectionStyles: Record<string, string> = {
  high: 'bg-confidence-high/10 border-l-4 border-l-confidence-high',
  medium: 'bg-confidence-medium/10 border-l-4 border-l-confidence-medium',
  low: 'bg-confidence-low/10 border-l-4 border-l-confidence-low',
}

function groupByPriority(requirements: Requirement[]): Record<string, Requirement[]> {
  const grouped: Record<string, Requirement[]> = {}
  for (const req of requirements) {
    if (!grouped[req.priority]) grouped[req.priority] = []
    grouped[req.priority].push(req)
  }
  return grouped
}

export function ComparisonMatrix({ results, onCellClick }: ComparisonMatrixProps) {
  const { matrix, rankings, requirements } = results
  if (!matrix || !rankings || !requirements) return null

  const sortedRankings = [...rankings].sort((a: VendorRanking, b: VendorRanking) => a.rank - b.rank)
  const vendors = sortedRankings.map(r => r.vendor)
  const grouped = groupByPriority(requirements)

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Comparison Matrix</h2>
      <div className="overflow-x-auto -mx-3 px-3">
        <table className="border-collapse w-full min-w-[600px]">
          <thead>
            <tr>
              <th className="bg-bg-table-header text-white text-xs p-2.5 text-left sticky top-0 z-10 border border-border-default">
                Requirement
              </th>
              {sortedRankings.map(r => (
                <th key={r.vendor} className="bg-bg-table-header text-white text-xs p-2.5 text-center sticky top-0 z-10 border border-border-default">
                  <Badge variant="rank">#{r.rank}</Badge>{' '}
                  {r.vendor}
                  <span className="block text-[10px] text-white/70 mt-0.5 font-normal">
                    {r.overall_score.toFixed(1)} / 100
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Interleaved: section header followed by its requirement rows */}
            {priorityOrder.flatMap(priority => {
              const reqs = grouped[priority] || []
              if (reqs.length === 0) return []
              return [
                <tr key={`section-${priority}`}>
                  <td colSpan={vendors.length + 1} className={`${prioritySectionStyles[priority] || ''} text-text-primary font-bold text-left p-2 text-sm border border-border-default`}>
                    {priorityLabels[priority]}
                  </td>
                </tr>,
                ...reqs.map(req => (
                  <tr key={req.id} className="even:bg-bg-primary/50">
                    <td className="text-left bg-bg-primary min-w-[200px] p-2.5 text-sm border border-border-default">
                      <span className="block font-mono text-xs text-text-tertiary">{req.id}</span>
                      <span className="block text-text-primary leading-snug">{req.description}</span>
                    </td>
                    {vendors.map(vendor => {
                      const scoreResult = matrix[vendor]?.[req.id]
                      if (scoreResult) {
                        return (
                          <ScoreCell
                            key={`${vendor}-${req.id}`}
                            score={scoreResult.score}
                            confidence={scoreResult.confidence}
                            status={scoreResult.status}
                            statusDetail={scoreResult.status_detail}
                            vendor={vendor}
                            requirementId={req.id}
                            requirementDesc={req.description}
                            onClick={onCellClick}
                          />
                        )
                      }
                      return <EmptyScoreCell key={`${vendor}-${req.id}`} />
                    })}
                  </tr>
                )),
              ]
            })}
          </tbody>
        </table>
      </div>

      {/* Legend — score and confidence only */}
      <div className="mt-2.5 p-3 bg-bg-primary rounded-sm text-xs text-text-secondary space-y-2">
        <div className="flex gap-4 flex-wrap items-center">
          <strong>Score (0-10):</strong>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-6 h-2 rounded-full bg-confidence-high" />
            High (7-10)
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-6 h-2 rounded-full bg-confidence-medium" />
            Medium (4-6.9)
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="w-6 h-2 rounded-full bg-confidence-low" />
            Low (&lt;4)
          </span>
        </div>

        <div className="flex gap-4 flex-wrap items-center">
          <strong>Confidence:</strong>
          <span className="inline-flex items-center gap-1.5">
            <span className="text-confidence-high font-medium">70%+</span>
            High
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="text-confidence-medium font-medium">40-69%</span>
            Medium
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="text-confidence-low font-medium">&lt;40%</span>
            Low
          </span>
          <span className="inline-flex items-center gap-1.5 text-text-tertiary italic">
            No evidence = searched, nothing found
          </span>
          <span className="inline-flex items-center gap-1.5 text-status-error">
            {'\u26A0'} Error = search failed
          </span>
        </div>
      </div>
    </div>
  )
}
