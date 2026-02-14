'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'

/**
 * Theme toggle button that cycles between light, dark, and system themes.
 * Shows sun icon in dark mode, moon icon in light mode.
 */
export function ThemeToggleButton() {
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme, systemTheme, resolvedTheme } = useTheme()

  // Prevent hydration mismatch by only rendering after mount
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    // Return a placeholder with same dimensions to prevent layout shift
    return (
      <button
        type="button"
        className="rounded-md p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
        aria-label="Toggle theme"
        disabled
      >
        <div className="h-5 w-5" />
      </button>
    )
  }

  const handleToggle = () => {
    // Cycle: light → dark → system → light
    if (theme === 'light') {
      setTheme('dark')
    } else if (theme === 'dark') {
      setTheme('system')
    } else {
      setTheme('light')
    }
  }

  const currentTheme = theme === 'system' ? systemTheme : resolvedTheme
  const isDark = currentTheme === 'dark'

  return (
    <button
      type="button"
      onClick={handleToggle}
      className="rounded-md p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'} theme`}
      title={`Current: ${theme}${theme === 'system' ? ` (${systemTheme})` : ''}`}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  )
}
