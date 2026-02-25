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
const priorityBadgeLabel: Record<string, string> = {
  high: 'H',
  medium: 'M',
  low: 'L',
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
                <th key={r.vendor} className="bg-bg-table-header text-white text-xs p-2.5 text-center sticky top-0 z-10 border border-border-default whitespace-pre-line">
                  <Badge variant="rank">#{r.rank}</Badge>{' '}
                  {r.vendor}
                  {'\n'}({r.overall_score.toFixed(1)})
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {priorityOrder.map(priority => {
              const reqs = grouped[priority] || []
              if (reqs.length === 0) return null
              return (
                <tr key={priority}>
                  <td colSpan={vendors.length + 1} className={`${prioritySectionStyles[priority] || ''} text-text-primary font-bold text-left p-2 text-sm border border-border-default`}>
                    {priorityLabels[priority]}
                  </td>
                </tr>
              ) as React.ReactNode
            }).concat(
              priorityOrder.flatMap(priority => {
                const reqs = grouped[priority] || []
                return reqs.map(req => (
                  <tr key={req.id} className="even:bg-bg-primary/50">
                    <td className="text-left font-medium bg-bg-primary min-w-[200px] p-2.5 text-sm border border-border-default">
                      <Badge variant="priority">{priorityBadgeLabel[req.priority] || 'M'}</Badge>{' '}
                      <span className="font-mono text-xs text-text-secondary">{req.id}</span>{' '}
                      {req.description}
                    </td>
                    {vendors.map(vendor => {
                      const scoreResult = matrix[vendor]?.[req.id]
                      if (scoreResult) {
                        return (
                          <ScoreCell
                            key={`${vendor}-${req.id}`}
                            score={scoreResult.score}
                            confidence={scoreResult.confidence}
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
                ))
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Confidence Legend */}
      <div className="mt-2.5 mb-5 p-2.5 bg-bg-primary rounded-sm text-xs text-text-secondary flex gap-5 flex-wrap">
        <strong>Confidence:</strong>
        <span className="inline-flex items-center gap-1">
          <span className="w-4 h-4 rounded-xs bg-text-tertiary border-2 border-text-primary" />
          High (&ge;0.7)
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-4 h-4 rounded-xs bg-text-tertiary border-2 border-dashed border-text-tertiary opacity-80" />
          Medium (0.4&ndash;0.69)
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-4 h-4 rounded-xs bg-text-tertiary border-2 border-dashed border-confidence-low opacity-60" />
          Low (&lt;0.4) &#9888;
        </span>
      </div>
    </div>
  )
}
