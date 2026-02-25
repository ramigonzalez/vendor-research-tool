import type { SourceInfo } from '../../hooks/useResearchState'
import { SourcePill } from '../molecules/SourcePill'

interface SourcesVisitedProps {
  sources: SourceInfo[]
}

export function SourcesVisited({ sources }: SourcesVisitedProps) {
  // Deduplicate by URL
  const uniqueByUrl = new Map<string, SourceInfo>()
  for (const s of sources) {
    if (!uniqueByUrl.has(s.url)) {
      uniqueByUrl.set(s.url, s)
    }
  }
  const uniqueSources = Array.from(uniqueByUrl.values())

  // Group by domain
  const byDomain = new Map<string, SourceInfo[]>()
  for (const s of uniqueSources) {
    if (!byDomain.has(s.domain)) byDomain.set(s.domain, [])
    byDomain.get(s.domain)!.push(s)
  }

  const sortedDomains = Array.from(byDomain.entries()).sort((a, b) => b[1].length - a[1].length)

  return (
    <div className="p-3">
      <div className="text-xs text-text-tertiary mb-3">
        Sources ({uniqueSources.length} unique from {sources.length} searches)
      </div>

      {uniqueSources.length === 0 ? (
        <p className="text-xs text-text-tertiary italic">No sources discovered yet.</p>
      ) : (
        <div className="space-y-3">
          {sortedDomains.map(([domain, domainSources]) => (
            <div key={domain}>
              <div className="text-xs font-medium text-text-secondary mb-1">
                {domain} ({domainSources.length})
              </div>
              <div className="flex flex-wrap gap-1.5 ml-2">
                {domainSources.map((s, i) => (
                  <SourcePill key={`${s.url}-${i}`} domain={s.domain} name={s.name} url={s.url} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
