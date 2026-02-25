import { useState } from 'react'

interface SourcePillProps {
  domain: string
  name: string
  url: string
}

export function SourcePill({ domain, name, url }: SourcePillProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-bg-secondary border border-border-subtle text-xs text-text-secondary hover:bg-bg-elevated hover:border-border-default transition-all animate-pill-enter no-underline"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Favicon with globe fallback */}
      <img
        src={`https://www.google.com/s2/favicons?domain=${domain}&sz=16`}
        alt=""
        className="w-3.5 h-3.5 rounded-full"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none'
        }}
      />
      <span className={`transition-all ${isHovered ? 'max-w-[300px]' : 'max-w-[120px]'} overflow-hidden text-ellipsis whitespace-nowrap`}>
        {isHovered ? name || domain : domain}
      </span>
    </a>
  )
}
