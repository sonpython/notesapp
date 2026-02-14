'use client'

import { useState, useCallback, useMemo } from 'react'
import { api } from '@/lib/api'
import type { Folder, PaginatedResponse } from '@/lib/types'

interface UseFoldersReturn {
  folders: Folder[]
  folderTree: Folder[]
  loading: boolean
  error: string | null
  total: number
  hasMore: boolean
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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch folders'
      setError(message)
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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load more folders'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [loading, hasMore, offset, limit])

  const createFolder = useCallback(async (name: string, parentId?: string): Promise<Folder> => {
    setError(null)
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
    fetchFolders,
    loadMore,
    createFolder,
    updateFolder,
    deleteFolder,
  }
}
