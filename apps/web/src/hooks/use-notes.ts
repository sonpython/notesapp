'use client'

import { useCallback, useState } from 'react'
import { api } from '@/lib/api'
import type { Note, PaginatedResponse } from '@/lib/types'
import * as notesDB from '@/lib/offline/indexed-db-notes'
import * as syncQueue from '@/lib/offline/indexed-db-sync-queue'

interface UseNotesReturn {
  notes: Note[]
  loading: boolean
  error: string | null
  total: number
  hasMore: boolean
  fromCache: boolean
  fetchNotes: (folderId?: string, search?: string, tagIds?: string[]) => Promise<void>
  loadMore: () => Promise<void>
  createNote: (data: Partial<Note>) => Promise<Note>
  updateNote: (id: string, data: Partial<Note>) => Promise<Note>
  deleteNote: (id: string) => Promise<void>
  moveNoteToFolder: (noteId: string, folderId: string | null) => Promise<void>
}

/**
 * Custom hook for managing notes CRUD operations.
 * Provides notes state, loading/error tracking, and API methods.
 */
export function useNotes(): UseNotesReturn {
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [limit] = useState(50)
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>()
  const [currentSearch, setCurrentSearch] = useState<string | undefined>()
  const [currentTagIds, setCurrentTagIds] = useState<string[] | undefined>()
  const [fromCache, setFromCache] = useState(false)

  const hasMore = notes.length < total

  const fetchNotes = useCallback(async (folderId?: string, search?: string, tagIds?: string[]) => {
    setLoading(true)
    setError(null)
    setOffset(0)
    setCurrentFolderId(folderId)
    setCurrentSearch(search)
    setCurrentTagIds(tagIds)
    try {
      const params = new URLSearchParams()
      if (folderId) params.set('folder_id', folderId)
      if (search) params.set('search', search)
      if (tagIds && tagIds.length > 0) params.set('tag_ids', tagIds.join(','))
      params.set('limit', limit.toString())
      params.set('offset', '0')
      const query = params.toString()
      const path = `/api/notes${query ? `?${query}` : ''}`
      const data = await api.get<PaginatedResponse<Note>>(path)
      setNotes(data.items)
      setTotal(data.total)
      setFromCache(false)
      // Write-through to IndexedDB
      await notesDB.putManyNotes(data.items).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch notes'
      setError(message)
      // Offline fallback: load from IndexedDB
      if (!navigator.onLine) {
        try {
          const cached = await notesDB.getAllNotes()
          setNotes(cached)
          setTotal(cached.length)
          setFromCache(true)
          setError(null) // Clear error if we have cached data
        } catch (cacheErr) {
          console.error('[use-notes] Failed to load from cache:', cacheErr)
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
      if (currentFolderId) params.set('folder_id', currentFolderId)
      if (currentSearch) params.set('search', currentSearch)
      if (currentTagIds && currentTagIds.length > 0) params.set('tag_ids', currentTagIds.join(','))
      params.set('limit', limit.toString())
      params.set('offset', newOffset.toString())
      const query = params.toString()
      const path = `/api/notes${query ? `?${query}` : ''}`
      const data = await api.get<PaginatedResponse<Note>>(path)
      setNotes(prev => [...prev, ...data.items])
      setTotal(data.total)
      setOffset(newOffset)
      // Write-through to IndexedDB
      await notesDB.putManyNotes(data.items).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load more notes'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [loading, hasMore, offset, limit, currentFolderId, currentSearch, currentTagIds])

  const createNote = useCallback(async (data: Partial<Note>): Promise<Note> => {
    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const tempNote: Note = {
        id: crypto.randomUUID(),
        user_id: '', // Will be set by server
        title: data.title || '',
        content: data.content || '',
        folder_id: data.folder_id || null,
        is_pinned: data.is_pinned || false,
        is_archived: data.is_archived || false,
        tags: data.tags || [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      await notesDB.putNote(tempNote)
      await syncQueue.enqueue({
        entity_type: 'note',
        operation: 'create',
        entity_id: tempNote.id,
        payload: data as Record<string, unknown>,
        timestamp: Date.now(),
        retry_count: 0,
      })
      setNotes(prev => [tempNote, ...prev])
      return tempNote
    }

    // Online: normal API call + write-through
    try {
      const created = await api.post<Note>('/api/notes', data)
      setNotes(prev => [created, ...prev])
      await notesDB.putNote(created).catch(console.error)
      return created
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create note'
      setError(message)
      throw err
    }
  }, [])

  const updateNote = useCallback(async (id: string, data: Partial<Note>): Promise<Note> => {
    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const existing = await notesDB.getNoteById(id)
      if (!existing) throw new Error('Note not found in local cache')

      const updated: Note = { ...existing, ...data, updated_at: new Date().toISOString() }
      await notesDB.putNote(updated)
      await syncQueue.enqueue({
        entity_type: 'note',
        operation: 'update',
        entity_id: id,
        payload: data as Record<string, unknown>,
        timestamp: Date.now(),
        retry_count: 0,
      })
      setNotes(prev => prev.map(n => (n.id === id ? updated : n)))
      return updated
    }

    // Online: normal API call + write-through
    try {
      const updated = await api.put<Note>(`/api/notes/${id}`, data)
      setNotes(prev => prev.map(n => (n.id === id ? updated : n)))
      await notesDB.putNote(updated).catch(console.error)
      return updated
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update note'
      setError(message)
      throw err
    }
  }, [])

  const deleteNote = useCallback(async (id: string): Promise<void> => {
    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      await notesDB.deleteNoteLocal(id)
      await syncQueue.enqueue({
        entity_type: 'note',
        operation: 'delete',
        entity_id: id,
        payload: null,
        timestamp: Date.now(),
        retry_count: 0,
      })
      setNotes(prev => prev.filter(n => n.id !== id))
      return
    }

    // Online: normal API call + write-through
    try {
      await api.delete(`/api/notes/${id}`)
      setNotes(prev => prev.filter(n => n.id !== id))
      await notesDB.deleteNoteLocal(id).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete note'
      setError(message)
      throw err
    }
  }, [])

  const moveNoteToFolder = useCallback(async (noteId: string, folderId: string | null): Promise<void> => {
    try {
      await api.put(`/api/notes/${noteId}`, { folder_id: folderId })
      // Refresh to update the note's folder
      setNotes(prev => prev.map(n => (n.id === noteId ? { ...n, folder_id: folderId } : n)))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to move note'
      setError(message)
      throw err
    }
  }, [])

  return { notes, loading, error, total, hasMore, fromCache, fetchNotes, loadMore, createNote, updateNote, deleteNote, moveNoteToFolder }
}
