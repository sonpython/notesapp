'use client'

import { useCallback, useState } from 'react'
import { api } from '@/lib/api'
import type { Note, PaginatedResponse } from '@/lib/types'

interface UseNotesReturn {
  notes: Note[]
  loading: boolean
  error: string | null
  total: number
  hasMore: boolean
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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch notes'
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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load more notes'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [loading, hasMore, offset, limit, currentFolderId, currentSearch, currentTagIds])

  const createNote = useCallback(async (data: Partial<Note>): Promise<Note> => {
    try {
      const created = await api.post<Note>('/api/notes', data)
      setNotes(prev => [created, ...prev])
      return created
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create note'
      setError(message)
      throw err
    }
  }, [])

  const updateNote = useCallback(async (id: string, data: Partial<Note>): Promise<Note> => {
    try {
      const updated = await api.put<Note>(`/api/notes/${id}`, data)
      setNotes(prev => prev.map(n => (n.id === id ? updated : n)))
      return updated
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update note'
      setError(message)
      throw err
    }
  }, [])

  const deleteNote = useCallback(async (id: string): Promise<void> => {
    try {
      await api.delete(`/api/notes/${id}`)
      setNotes(prev => prev.filter(n => n.id !== id))
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

  return { notes, loading, error, total, hasMore, fetchNotes, loadMore, createNote, updateNote, deleteNote, moveNoteToFolder }
}
