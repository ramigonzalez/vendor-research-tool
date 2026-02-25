import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeContextValue {
  theme: ThemeMode
  setTheme: (mode: ThemeMode) => void
  resolvedTheme: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

const STORAGE_KEY = 'vrt-theme-preference'
const DARK_MQ = '(prefers-color-scheme: dark)'

function getSystemPreference(): 'light' | 'dark' {
  return window.matchMedia(DARK_MQ).matches ? 'dark' : 'light'
}

function applyTheme(resolved: 'light' | 'dark') {
  document.documentElement.classList.toggle('dark', resolved === 'dark')
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
    return 'system'
  })

  const resolvedTheme = theme === 'system' ? getSystemPreference() : theme

  const setTheme = useCallback((mode: ThemeMode) => {
    setThemeState(mode)
    localStorage.setItem(STORAGE_KEY, mode)
  }, [])

  // Apply dark class whenever resolved theme changes
  useEffect(() => {
    applyTheme(resolvedTheme)
  }, [resolvedTheme])

  // Listen for OS theme changes when in system mode
  useEffect(() => {
    if (theme !== 'system') return

    const mq = window.matchMedia(DARK_MQ)
    const handler = (e: MediaQueryListEvent) => {
      applyTheme(e.matches ? 'dark' : 'light')
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
