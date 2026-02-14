'use client'

import { useCallback, useState } from 'react'
import { api } from '@/lib/api'
import type { Note } from '@/lib/types'

interface UseNotesReturn {
  notes: Note[]
  loading: boolean
  error: string | null
  fetchNotes: (folderId?: string, search?: string) => Promise<void>
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

  const fetchNotes = useCallback(async (folderId?: string, search?: string) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (folderId) params.set('folder_id', folderId)
      if (search) params.set('search', search)
      const query = params.toString()
      const path = `/api/notes${query ? `?${query}` : ''}`
      const data = await api.get<Note[]>(path)
      setNotes(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch notes'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

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

  return { notes, loading, error, fetchNotes, createNote, updateNote, deleteNote, moveNoteToFolder }
}
