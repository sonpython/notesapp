'use client'
import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Tag } from '@/lib/types'

interface CreateTagData {
  name: string
  color?: string
}

interface UpdateTagData {
  name?: string
  color?: string
}

export function useTags() {
  const [tags, setTags] = useState<Tag[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTags = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<Tag[]>('/api/tags')
      setTags(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tags')
    } finally {
      setLoading(false)
    }
  }, [])

  const createTag = useCallback(async (data: CreateTagData): Promise<Tag | null> => {
    try {
      const tag = await api.post<Tag>('/api/tags', data)
      setTags(prev => [...prev, tag])
      return tag
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create tag')
      return null
    }
  }, [])

  const updateTag = useCallback(async (id: string, data: UpdateTagData): Promise<Tag | null> => {
    try {
      const tag = await api.put<Tag>(`/api/tags/${id}`, data)
      setTags(prev => prev.map(t => t.id === id ? tag : t))
      return tag
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update tag')
      return null
    }
  }, [])

  const deleteTag = useCallback(async (id: string): Promise<boolean> => {
    try {
      await api.delete(`/api/tags/${id}`)
      setTags(prev => prev.filter(t => t.id !== id))
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete tag')
      return false
    }
  }, [])

  // Tag assignment helpers (for notes/todos)
  const addTagToNote = useCallback(async (noteId: string, tagIds: string[]) => {
    await api.post(`/api/notes/${noteId}/tags`, { tag_ids: tagIds })
  }, [])

  const removeTagFromNote = useCallback(async (noteId: string, tagId: string) => {
    await api.delete(`/api/notes/${noteId}/tags/${tagId}`)
  }, [])

  const addTagToTodo = useCallback(async (todoId: string, tagIds: string[]) => {
    await api.post(`/api/todos/${todoId}/tags`, { tag_ids: tagIds })
  }, [])

  const removeTagFromTodo = useCallback(async (todoId: string, tagId: string) => {
    await api.delete(`/api/todos/${todoId}/tags/${tagId}`)
  }, [])

  return {
    tags,
    loading,
    error,
    fetchTags,
    createTag,
    updateTag,
    deleteTag,
    addTagToNote,
    removeTagFromNote,
    addTagToTodo,
    removeTagFromTodo,
  }
}
