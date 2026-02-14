'use client'

import { useCallback, useState } from 'react'
import { AppSidebar } from './app-sidebar'
import { AppHeader } from './app-header'
import { ResizableDivider } from '@/components/ui/resizable-divider'

const SIDEBAR_WIDTH_KEY = 'notesapp-sidebar-width'
const DEFAULT_SIDEBAR_WIDTH = 256 // 64 * 4 = 256px (w-64)
const MIN_SIDEBAR_WIDTH = 200
const MAX_SIDEBAR_WIDTH = 400

interface ResizableAppLayoutProps {
  children: React.ReactNode
}

/**
 * Resizable app layout with sidebar, divider, and main content.
 * Sidebar width is persisted to localStorage.
 */
export function ResizableAppLayout({ children }: ResizableAppLayoutProps) {
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    if (typeof window === 'undefined') return DEFAULT_SIDEBAR_WIDTH
    const saved = localStorage.getItem(SIDEBAR_WIDTH_KEY)
    return saved ? parseInt(saved, 10) : DEFAULT_SIDEBAR_WIDTH
  })

  const handleSidebarResize = useCallback((newWidth: number) => {
    const clampedWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(MAX_SIDEBAR_WIDTH, newWidth))
    setSidebarWidth(clampedWidth)
    localStorage.setItem(SIDEBAR_WIDTH_KEY, clampedWidth.toString())
  }, [])

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Mobile header with menu toggle */}
      <AppHeader />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar - hidden on mobile */}
        <div className="hidden lg:block" style={{ width: sidebarWidth }}>
          <AppSidebar />
        </div>

        {/* Resizable divider - hidden on mobile */}
        <div className="hidden lg:block">
          <ResizableDivider onResize={handleSidebarResize} />
        </div>

        {/* Main content area: note list + editor panes rendered by children */}
        <main className="flex flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
