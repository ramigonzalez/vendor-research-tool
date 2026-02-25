interface BadgeProps {
  variant: 'rank' | 'status' | 'source-type' | 'priority'
  children: React.ReactNode
  className?: string
}

const variantStyles: Record<BadgeProps['variant'], string> = {
  rank: 'bg-white/25 text-white px-2 py-0.5 rounded-full text-xs font-bold',
  status: 'px-2 py-0.5 rounded text-xs font-bold uppercase text-white',
  'source-type': 'px-1.5 py-0.5 rounded text-xs text-white',
  priority: 'px-1.5 py-0.5 rounded-xs text-xs font-semibold',
}

const priorityColors: Record<string, string> = {
  H: 'bg-confidence-high text-white',
  M: 'bg-confidence-medium text-white',
  L: 'bg-confidence-low text-white',
}

const statusColors: Record<string, string> = {
  completed: 'bg-status-complete',
  running: 'bg-accent-tertiary',
  failed: 'bg-status-error',
  pending: 'bg-text-tertiary',
}

const sourceTypeColors: Record<string, string> = {
  official_docs: 'bg-accent-tertiary',
  github: 'bg-text-primary',
  comparison: 'bg-status-analyzing',
  blog: 'bg-confidence-medium',
  community: 'bg-text-tertiary',
}

export function Badge({ variant, children, className = '' }: BadgeProps) {
  const text = typeof children === 'string' ? children : ''
  let colorClass = ''

  if (variant === 'priority') {
    colorClass = priorityColors[text] || 'bg-text-tertiary text-white'
  } else if (variant === 'status') {
    colorClass = statusColors[text] || 'bg-text-tertiary'
  } else if (variant === 'source-type') {
    colorClass = sourceTypeColors[text] || 'bg-text-tertiary'
  }

  return (
    <span className={`inline-block ${variantStyles[variant]} ${colorClass} ${className}`}>
      {children}
    </span>
  )
}
