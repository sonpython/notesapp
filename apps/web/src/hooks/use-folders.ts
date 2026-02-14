'use client'

import { useState, useCallback, useMemo } from 'react'
import { api } from '@/lib/api'
import type { Folder, PaginatedResponse } from '@/lib/types'
import * as foldersDB from '@/lib/offline/indexed-db-folders'
import * as syncQueue from '@/lib/offline/indexed-db-sync-queue'

interface UseFoldersReturn {
  folders: Folder[]
  folderTree: Folder[]
  loading: boolean
  error: string | null
  total: number
  hasMore: boolean
  fromCache: boolean
  fetchFolders: () => Promise<void>
  loadMore: () => Promise<void>
  createFolder: (name: string, parentId?: string) => Promise<Folder>
  updateFolder: (id: string, data: { name?: string; parent_id?: string | null }) => Promise<Folder>
  deleteFolder: (id: string) => Promise<void>
}

/**
 * Build hierarchical folder tree from flat list.
 * Folders with parent_id are nested under their parent's children array.
 * Returns only root-level folders (parent_id === null).
 */
function buildFolderTree(folders: Folder[]): Folder[] {
  const folderMap = new Map<string, Folder>()

  // Clone folders and initialize children arrays
  folders.forEach(folder => {
    folderMap.set(folder.id, { ...folder, children: [] })
  })

  const roots: Folder[] = []

  // Build tree by assigning children to parents
  folderMap.forEach(folder => {
    if (folder.parent_id) {
      const parent = folderMap.get(folder.parent_id)
      if (parent) {
        parent.children!.push(folder)
      } else {
        // Orphaned folder (parent deleted) -> treat as root
        roots.push(folder)
      }
    } else {
      roots.push(folder)
    }
  })

  return roots
}

/**
 * Custom hook for managing folders CRUD operations.
 * Provides flat list and nested tree structure from API data.
 */
export function useFolders(): UseFoldersReturn {
  const [folders, setFolders] = useState<Folder[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [limit] = useState(50)
  const [fromCache, setFromCache] = useState(false)

  const hasMore = folders.length < total

  // Derive tree structure from flat list
  const folderTree = useMemo(() => buildFolderTree(folders), [folders])

  const fetchFolders = useCallback(async () => {
    setLoading(true)
    setError(null)
    setOffset(0)
    try {
      const params = new URLSearchParams()
      params.set('limit', limit.toString())
      params.set('offset', '0')
      const query = params.toString()
      const data = await api.get<PaginatedResponse<Folder>>(`/api/folders?${query}`)
      setFolders(data.items)
      setTotal(data.total)
      setFromCache(false)
      // Write-through to IndexedDB
      await foldersDB.putManyFolders(data.items).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch folders'
      setError(message)
      // Offline fallback: load from IndexedDB
      if (!navigator.onLine) {
        try {
          const cached = await foldersDB.getAllFolders()
          setFolders(cached)
          setTotal(cached.length)
          setFromCache(true)
          setError(null)
        } catch (cacheErr) {
          console.error('[use-folders] Failed to load from cache:', cacheErr)
        }
      }
    } finally {
      setLoading(false)
    }
  }, [limit])

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return
    setLoading(true)
    setError(null)
    try {
      const newOffset = offset + limit
      const params = new URLSearchParams()
      params.set('limit', limit.toString())
      params.set('offset', newOffset.toString())
      const query = params.toString()
      const data = await api.get<PaginatedResponse<Folder>>(`/api/folders?${query}`)
      setFolders(prev => [...prev, ...data.items])
      setTotal(data.total)
      setOffset(newOffset)
      // Write-through to IndexedDB
      await foldersDB.putManyFolders(data.items).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load more folders'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [loading, hasMore, offset, limit])

  const createFolder = useCallback(async (name: string, parentId?: string): Promise<Folder> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const tempFolder: Folder = {
        id: crypto.randomUUID(),
        user_id: '',
        name,
        parent_id: parentId || null,
        icon: null,
        children: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      await foldersDB.putFolder(tempFolder)
      await syncQueue.enqueue({
        entity_type: 'folder',
        operation: 'create',
        entity_id: tempFolder.id,
        payload: { name, parent_id: parentId || null },
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchFolders()
      return tempFolder
    }

    // Online: normal API call
    try {
      const created = await api.post<Folder>('/api/folders', {
        name,
        parent_id: parentId || null,
      })
      await fetchFolders()
      return created
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create folder'
      setError(message)
      throw err
    }
  }, [fetchFolders])

  const updateFolder = useCallback(async (
    id: string,
    data: { name?: string; parent_id?: string | null }
  ): Promise<Folder> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const existing = await foldersDB.getFolderById(id)
      if (!existing) throw new Error('Folder not found in local cache')

      const updated: Folder = { ...existing, ...data, updated_at: new Date().toISOString() }
      await foldersDB.putFolder(updated)
      await syncQueue.enqueue({
        entity_type: 'folder',
        operation: 'update',
        entity_id: id,
        payload: data as Record<string, unknown>,
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchFolders()
      return updated
    }

    // Online: normal API call
    try {
      const updated = await api.put<Folder>(`/api/folders/${id}`, data)
      await fetchFolders()
      return updated
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update folder'
      setError(message)
      throw err
    }
  }, [fetchFolders])

  const deleteFolder = useCallback(async (id: string): Promise<void> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      await foldersDB.deleteFolderLocal(id)
      await syncQueue.enqueue({
        entity_type: 'folder',
        operation: 'delete',
        entity_id: id,
        payload: null,
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchFolders()
      return
    }

    // Online: normal API call
    try {
      await api.delete(`/api/folders/${id}`)
      await fetchFolders()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete folder'
      setError(message)
      throw err
    }
  }, [fetchFolders])

  return {
    folders,
    folderTree,
    loading,
    error,
    total,
    hasMore,
    fromCache,
    fetchFolders,
    loadMore,
    createFolder,
    updateFolder,
    deleteFolder,
  }
}
