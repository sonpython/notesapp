'use client'

import { useState } from 'react'
import { Menu, X } from 'lucide-react'
import { AppSidebar } from '@/components/layout/app-sidebar'

/**
 * Mobile/tablet header with menu toggle for the sidebar.
 * Hidden on desktop screens (lg:hidden).
 */
export function AppHeader() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <>
      {/* Header bar - visible on mobile/tablet only */}
      <header className="flex h-12 items-center justify-between border-b border-border bg-background px-4 lg:hidden">
        <h1 className="text-sm font-semibold text-foreground">NotesApp</h1>
        <button
          type="button"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="rounded-md p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
          aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
        >
          {sidebarOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </header>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40 bg-black/60 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          {/* Sidebar panel */}
          <div className="fixed inset-y-0 left-0 z-50 w-64 lg:hidden">
            <AppSidebar />
          </div>
        </>
      )}
    </>
  )
}
