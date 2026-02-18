// Sync engine for replaying queued mutations when connection is restored
import { api } from '$lib/api'
import * as syncQueue from './indexed-db-sync-queue'
import * as notesDB from './indexed-db-notes'
import * as todosDB from './indexed-db-todos'
import * as foldersDB from './indexed-db-folders'
import type { SyncQueueEntry } from './offline-types'
import type { Note, Todo, Folder } from '$lib/types'

const MAX_RETRIES = 3

let onlineListener: (() => void) | null = null

/**
 * Replay all pending mutations from sync queue.
 * Processes entries sequentially to preserve operation order.
 * Returns count of successful and failed operations.
 */
export async function replayQueue(): Promise<{ success: number; failed: number }> {
  const entries = await syncQueue.getAllPending()
  let success = 0
  let failed = 0

  for (const entry of entries) {
    if (entry.retry_count >= MAX_RETRIES) {
      console.warn(`[sync] Max retries reached for entry ${entry.id}`, entry)
      failed++
      continue
    }

    try {
      const serverData = await executeEntry(entry)
      await syncQueue.dequeue(entry.id!)

      // Update local IndexedDB with server response (replace temp data)
      if (serverData) {
        await updateLocalStore(entry.entity_type, entry.operation, serverData)
      }

      success++
    } catch (err) {
      console.error(`[sync] Failed to replay entry ${entry.id}:`, err)
      await syncQueue.updateRetryCount(entry.id!, entry.retry_count + 1)
      failed++
    }
  }

  console.log(`[sync] Replay complete: ${success} success, ${failed} failed`)
  return { success, failed }
}

/**
 * Execute a single sync queue entry via API.
 * Returns server response data for local store update.
 */
async function executeEntry(entry: SyncQueueEntry): Promise<Note | Todo | Folder | null> {
  const { entity_type, operation, entity_id, payload } = entry
  const basePath = `/api/${entity_type}s` // notes, todos, folders

  switch (operation) {
    case 'create':
      return await api.post(basePath, payload)

    case 'update':
      return await api.put(`${basePath}/${entity_id}`, payload)

    case 'delete':
      await api.delete(`${basePath}/${entity_id}`)
      return null

    default:
      throw new Error(`Unknown operation: ${operation}`)
  }
}

/**
 * Update local IndexedDB store with server response.
 * For creates: replace temp entry with server entry (has real ID).
 * For updates: update with server data.
 * For deletes: already handled in mutation.
 */
async function updateLocalStore(
  entityType: string,
  operation: string,
  serverData: Note | Todo | Folder | null
): Promise<void> {
  if (!serverData) return

  switch (entityType) {
    case 'note':
      await notesDB.putNote(serverData as Note)
      break
    case 'todo':
      await todosDB.putTodo(serverData as Todo)
      break
    case 'folder':
      await foldersDB.putFolder(serverData as Folder)
      break
  }
}

/**
 * Fetch fresh data from server and replace all local stores.
 * Called after successful queue replay to ensure consistency.
 */
export async function fullRefresh(): Promise<void> {
  try {
    // Fetch all entities from server
    const [notesRes, todosRes, foldersRes] = await Promise.all([
      api.get<{ items: Note[]; total: number }>('/api/notes?limit=1000'),
      api.get<{ items: Todo[]; total: number }>('/api/todos?limit=1000'),
      api.get<{ items: Folder[]; total: number }>('/api/folders?limit=1000'),
    ])

    // Replace local stores with fresh data
    await Promise.all([
      notesDB.clearNotes().then(() => notesDB.putManyNotes(notesRes.items)),
      todosDB.clearTodos().then(() => todosDB.putManyTodos(todosRes.items)),
      foldersDB.clearFolders().then(() => foldersDB.putManyFolders(foldersRes.items)),
    ])

    console.log('[sync] Full refresh complete')
  } catch (err) {
    console.error('[sync] Full refresh failed:', err)
    throw err
  }
}

/**
 * Start auto-sync on reconnect.
 * Listens for 'online' event and triggers replay + refresh.
 */
export function startAutoSync(): void {
  if (onlineListener) {
    console.warn('[sync] Auto-sync already started')
    return
  }

  onlineListener = async () => {
    console.log('[sync] Connection restored, starting sync...')
    try {
      const result = await replayQueue()
      if (result.success > 0 || result.failed > 0) {
        console.log('[sync] Refreshing local data after queue replay...')
        await fullRefresh()
      }
    } catch (err) {
      console.error('[sync] Auto-sync failed:', err)
    }
  }

  window.addEventListener('online', onlineListener)
  console.log('[sync] Auto-sync started')
}

/**
 * Stop auto-sync listener.
 * Call this on logout or unmount.
 */
export function stopAutoSync(): void {
  if (onlineListener) {
    window.removeEventListener('online', onlineListener)
    onlineListener = null
    console.log('[sync] Auto-sync stopped')
  }
}
