import type { QueryInfo } from '../../hooks/useResearchState'

interface QueryHistoryProps {
  queries: QueryInfo[]
}

export function QueryHistory({ queries }: QueryHistoryProps) {
  // Group by vendor -> requirement
  const grouped = new Map<string, Map<string, QueryInfo[]>>()
  for (const q of queries) {
    if (!grouped.has(q.vendor)) grouped.set(q.vendor, new Map())
    const vendorMap = grouped.get(q.vendor)!
    if (!vendorMap.has(q.requirementId)) vendorMap.set(q.requirementId, [])
    vendorMap.get(q.requirementId)!.push(q)
  }

  return (
    <div className="p-4">
      {queries.length === 0 ? (
        <p className="text-xs text-text-tertiary italic">No queries generated yet.</p>
      ) : (
        <div className="space-y-4">
        {Array.from(grouped.entries()).map(([vendor, reqMap]) => (
          <div key={vendor}>
            <h4 className="text-sm font-semibold text-text-primary mb-2">{vendor}</h4>
            {Array.from(reqMap.entries()).map(([reqId, queryInfos]) => (
              <div key={reqId} className="ml-3 mb-2">
                <div className="text-xs font-medium text-text-secondary mb-0.5">{reqId}</div>
                {queryInfos.map((qi, i) => (
                  <div key={i} className="ml-3">
                    {qi.queries.map((q, j) => (
                      <div key={j} className="text-xs text-text-tertiary py-0.5 flex items-start gap-1.5">
                        <span className="text-text-tertiary">&#8226;</span>
                        <span className="flex-1">{q}</span>
                        {qi.isRefined && (
                          <span className="text-[10px] bg-status-warning/20 text-status-warning px-1 py-0.5 rounded-xs">
                            Refined
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}
        </div>
      )}
    </div>
  )
}
