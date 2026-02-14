'use client'

import { CloudOff } from 'lucide-react'
import { useOnlineStatus } from '@/hooks/use-online-status'

/**
 * Offline status indicator that appears when network is disconnected.
 * Shows a small pill badge with cloud-off icon and "Offline" text.
 * Automatically hides when online.
 */
export function OfflineIndicator() {
  const { isOnline } = useOnlineStatus()

  if (isOnline) {
    return null
  }

  return (
    <div className="flex items-center gap-1.5 rounded-full border border-amber-800 bg-amber-900/30 px-3 py-1 text-xs font-medium text-amber-400 transition-all">
      <CloudOff className="h-3.5 w-3.5" />
      <span>Offline</span>
    </div>
  )
}
