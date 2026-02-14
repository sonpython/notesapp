'use client'

import { useState } from 'react'
import { Download, X, Share } from 'lucide-react'
import { useInstallPrompt } from '@/hooks/use-install-prompt'

const DISMISSED_KEY = 'pwa-install-dismissed'

/**
 * Banner prompting users to install the PWA.
 * Shows when app is installable and user hasn't dismissed it.
 * Handles both Chrome/Edge (beforeinstallprompt) and iOS (manual instructions).
 */
export function InstallBanner() {
  const { canInstall, isIOS, install } = useInstallPrompt()
  const [isDismissed, setIsDismissed] = useState(() => {
    // Check if user has previously dismissed the banner
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem(DISMISSED_KEY) !== null
    }
    return false
  })

  const handleDismiss = () => {
    setIsDismissed(true)
    sessionStorage.setItem(DISMISSED_KEY, 'true')
  }

  const handleInstall = async () => {
    await install()
    handleDismiss()
  }

  // Don't show if dismissed or if neither installable nor iOS
  if (isDismissed || (!canInstall && !isIOS)) {
    return null
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-sidebar p-4 shadow-lg lg:left-64">
      <div className="mx-auto flex max-w-4xl items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
            <Download className="h-5 w-5 text-accent" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-foreground">
              Install NotesApp
            </p>
            <p className="text-xs text-muted">
              {isIOS
                ? 'Tap Share button, then "Add to Home Screen"'
                : 'Install for offline access and faster performance'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {canInstall && (
            <button
              type="button"
              onClick={handleInstall}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90"
            >
              Install
            </button>
          )}
          {isIOS && (
            <div className="flex items-center gap-1 rounded-lg border border-border px-3 py-2">
              <Share className="h-4 w-4 text-accent" />
              <span className="text-xs font-medium text-accent">Share</span>
            </div>
          )}
          <button
            type="button"
            onClick={handleDismiss}
            className="rounded-md p-2 text-muted transition-colors hover:bg-zinc-800 hover:text-foreground"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
