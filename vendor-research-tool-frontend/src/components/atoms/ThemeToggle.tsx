import { useTheme } from '../../contexts/ThemeContext'

const modes = [
  { value: 'light' as const, icon: '\u2600', label: 'Light' },
  { value: 'dark' as const, icon: '\uD83C\uDF19', label: 'Dark' },
  { value: 'system' as const, icon: '\uD83D\uDCBB', label: 'System' },
]

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="inline-flex rounded-sm border border-border-default overflow-hidden" role="radiogroup" aria-label="Theme preference">
      {modes.map(mode => {
        const isActive = theme === mode.value
        return (
          <button
            key={mode.value}
            role="radio"
            aria-checked={isActive}
            onClick={() => setTheme(mode.value)}
            className={`px-2.5 py-1.5 text-xs cursor-pointer border-none transition-colors flex items-center gap-1.5
              ${isActive
                ? 'bg-accent-primary text-white'
                : 'bg-bg-secondary text-text-secondary hover:bg-bg-primary'
              }
            `}
          >
            <span aria-hidden="true">{mode.icon}</span>
            <span className="hidden sm:inline">{mode.label}</span>
          </button>
        )
      })}
    </div>
  )
}
