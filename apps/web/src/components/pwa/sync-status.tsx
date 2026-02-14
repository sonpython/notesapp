'use client'

import { useState, useEffect } from 'react'
import { RefreshCw, CheckCircle } from 'lucide-react'
import { useOnlineStatus } from '@/hooks/use-online-status'

/**
 * Sync status indicator showing pending changes and sync state.
 * Shows pending count when offline, syncing animation when syncing,
 * and auto-hides when all synced.
 */
export function SyncStatus() {
  const { isOnline } = useOnlineStatus()
  const [pendingCount, setPendingCount] = useState(0)
  const [isSyncing, setIsSyncing] = useState(false)

  useEffect(() => {
    // TODO: Connect to IndexedDB sync queue to get actual pending count
    // For now, simulate based on online status
    const checkPendingChanges = async () => {
      try {
        // Placeholder: In Phase 3, this would query the sync-queue store
        // const queue = await getAllFromSyncQueue()
        // setPendingCount(queue.length)
        setPendingCount(0)
      } catch (error) {
        console.error('Failed to check sync queue:', error)
        setPendingCount(0)
      }
    }

    checkPendingChanges()

    // Poll every 5 seconds when offline
    if (!isOnline) {
      const interval = setInterval(checkPendingChanges, 5000)
      return () => clearInterval(interval)
    }
  }, [isOnline])

  useEffect(() => {
    // When coming back online, show syncing state briefly
    if (isOnline && pendingCount > 0) {
      // TODO: This should be triggered by actual sync events from Phase 3
      const timeout = setTimeout(() => {
        setIsSyncing(true)
        setTimeout(() => {
          setIsSyncing(false)
          setPendingCount(0)
        }, 2000)
      }, 0)
      return () => clearTimeout(timeout)
    }
  }, [isOnline, pendingCount])

  // Don't show if nothing pending and not syncing
  if (pendingCount === 0 && !isSyncing) {
    return null
  }

  return (
    <div className="flex items-center gap-1.5 rounded-full border border-border bg-sidebar px-3 py-1 text-xs font-medium text-muted transition-all">
      {isSyncing ? (
        <>
          <RefreshCw className="h-3.5 w-3.5 animate-spin text-accent" />
          <span className="text-accent">Syncing...</span>
        </>
      ) : pendingCount > 0 ? (
        <>
          <RefreshCw className="h-3.5 w-3.5" />
          <span>
            {pendingCount} {pendingCount === 1 ? 'change' : 'changes'} pending
          </span>
        </>
      ) : (
        <>
          <CheckCircle className="h-3.5 w-3.5 text-green-400" />
          <span className="text-green-400">All synced</span>
        </>
      )}
    </div>
  )
}
