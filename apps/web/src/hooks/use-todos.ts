'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Todo, PaginatedResponse } from '@/lib/types'
import * as todosDB from '@/lib/offline/indexed-db-todos'
import * as syncQueue from '@/lib/offline/indexed-db-sync-queue'

/** Filter type for todo list views */
export type TodoFilter = 'all' | 'active' | 'completed' | 'overdue'

interface CreateTodoData {
  title: string
  description?: string
  priority?: number
  deadline?: string
  parent_id?: string
  reminder_at?: string
  recurrence_type?: string
  recurrence_interval?: number
  recurrence_days?: string
  recurrence_end_date?: string
}

interface UpdateTodoData {
  title?: string
  description?: string
  priority?: number
  deadline?: string
  is_completed?: boolean
  reminder_at?: string
  recurrence_type?: string
  recurrence_interval?: number
  recurrence_days?: string
  recurrence_end_date?: string
}

/**
 * Custom hook for managing todo CRUD operations and state.
 * Provides fetch, create, update, delete, and toggle actions
 * with loading/error tracking.
 */
export function useTodos() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<TodoFilter>('all')
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [limit] = useState(50)
  const [currentTagIds, setCurrentTagIds] = useState<string[] | undefined>()
  const [fromCache, setFromCache] = useState(false)

  const hasMore = todos.length < total

  const fetchTodos = useCallback(async (activeFilter?: TodoFilter, tagIds?: string[]) => {
    setLoading(true)
    setError(null)
    setOffset(0)
    setCurrentTagIds(tagIds)
    try {
      const filterParam = activeFilter || filter
      const params = new URLSearchParams()
      if (filterParam !== 'all') params.set('filter', filterParam)
      if (tagIds && tagIds.length > 0) params.set('tag_ids', tagIds.join(','))
      params.set('limit', limit.toString())
      params.set('offset', '0')
      const query = params.toString()
      const data = await api.get<PaginatedResponse<Todo>>(`/api/todos${query ? `?${query}` : ''}`)
      setTodos(data.items)
      setTotal(data.total)
      setFromCache(false)
      // Write-through to IndexedDB
      await todosDB.putManyTodos(data.items).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch todos'
      setError(message)
      // Offline fallback: load from IndexedDB
      if (!navigator.onLine) {
        try {
          const cached = await todosDB.getAllTodos()
          setTodos(cached)
          setTotal(cached.length)
          setFromCache(true)
          setError(null)
        } catch (cacheErr) {
          console.error('[use-todos] Failed to load from cache:', cacheErr)
        }
      }
    } finally {
      setLoading(false)
    }
  }, [filter, limit])

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return
    setLoading(true)
    setError(null)
    try {
      const newOffset = offset + limit
      const params = new URLSearchParams()
      if (filter !== 'all') params.set('filter', filter)
      if (currentTagIds && currentTagIds.length > 0) params.set('tag_ids', currentTagIds.join(','))
      params.set('limit', limit.toString())
      params.set('offset', newOffset.toString())
      const query = params.toString()
      const data = await api.get<PaginatedResponse<Todo>>(`/api/todos${query ? `?${query}` : ''}`)
      setTodos(prev => [...prev, ...data.items])
      setTotal(data.total)
      setOffset(newOffset)
      // Write-through to IndexedDB
      await todosDB.putManyTodos(data.items).catch(console.error)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load more todos'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [loading, hasMore, offset, limit, filter, currentTagIds])

  const createTodo = useCallback(async (data: CreateTodoData): Promise<Todo | null> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const tempTodo: Todo = {
        id: crypto.randomUUID(),
        user_id: '',
        title: data.title,
        description: data.description || null,
        priority: data.priority || 3,
        deadline: data.deadline || null,
        is_completed: false,
        completed_at: null,
        parent_id: data.parent_id || null,
        note_id: null,
        sort_order: 0,
        reminder_at: data.reminder_at || null,
        reminder_sent: false,
        recurrence_type: data.recurrence_type || null,
        recurrence_interval: data.recurrence_interval || null,
        recurrence_days: data.recurrence_days || null,
        recurrence_end_date: data.recurrence_end_date || null,
        recurrence_parent_id: null,
        tags: [],
        children: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      await todosDB.putTodo(tempTodo)
      await syncQueue.enqueue({
        entity_type: 'todo',
        operation: 'create',
        entity_id: tempTodo.id,
        payload: data as unknown as Record<string, unknown>,
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchTodos()
      return tempTodo
    }

    // Online: normal API call
    try {
      const todo = await api.post<Todo>('/api/todos', data)
      await fetchTodos()
      return todo
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create todo'
      setError(message)
      return null
    }
  }, [fetchTodos])

  const updateTodo = useCallback(async (
    id: string,
    data: UpdateTodoData
  ): Promise<Todo | null> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const existing = await todosDB.getTodoById(id)
      if (!existing) {
        setError('Todo not found in local cache')
        return null
      }
      const updated: Todo = { ...existing, ...data, updated_at: new Date().toISOString() }
      await todosDB.putTodo(updated)
      await syncQueue.enqueue({
        entity_type: 'todo',
        operation: 'update',
        entity_id: id,
        payload: data as unknown as Record<string, unknown>,
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchTodos()
      return updated
    }

    // Online: normal API call
    try {
      const todo = await api.put<Todo>(`/api/todos/${id}`, data)
      await fetchTodos()
      return todo
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update todo'
      setError(message)
      return null
    }
  }, [fetchTodos])

  const deleteTodo = useCallback(async (id: string): Promise<boolean> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      await todosDB.deleteTodoLocal(id)
      await syncQueue.enqueue({
        entity_type: 'todo',
        operation: 'delete',
        entity_id: id,
        payload: null,
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchTodos()
      return true
    }

    // Online: normal API call
    try {
      await api.delete(`/api/todos/${id}`)
      await fetchTodos()
      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete todo'
      setError(message)
      return false
    }
  }, [fetchTodos])

  const toggleTodo = useCallback(async (id: string): Promise<Todo | null> => {
    setError(null)

    // Offline: queue + local optimistic update
    if (!navigator.onLine) {
      const existing = await todosDB.getTodoById(id)
      if (!existing) {
        // Try to find in nested children for offline
        const target = findTodoById(todos, id)
        if (!target) {
          setError('Todo not found in local cache')
          return null
        }
        const updated: Todo = {
          ...target,
          is_completed: !target.is_completed,
          completed_at: !target.is_completed ? new Date().toISOString() : null,
          updated_at: new Date().toISOString(),
        }
        await todosDB.putTodo(updated)
        await syncQueue.enqueue({
          entity_type: 'todo',
          operation: 'update',
          entity_id: id,
          payload: { is_completed: updated.is_completed },
          timestamp: Date.now(),
          retry_count: 0,
        })
        await fetchTodos()
        return updated
      }
      const updated: Todo = {
        ...existing,
        is_completed: !existing.is_completed,
        completed_at: !existing.is_completed ? new Date().toISOString() : null,
        updated_at: new Date().toISOString(),
      }
      await todosDB.putTodo(updated)
      await syncQueue.enqueue({
        entity_type: 'todo',
        operation: 'update',
        entity_id: id,
        payload: { is_completed: updated.is_completed },
        timestamp: Date.now(),
        retry_count: 0,
      })
      await fetchTodos()
      return updated
    }

    // Online: use dedicated toggle endpoint (handles nested children correctly)
    try {
      const todo = await api.post<Todo>(`/api/todos/${id}/toggle`)
      await fetchTodos()
      return todo
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to toggle todo'
      setError(message)
      return null
    }
  }, [todos, fetchTodos])

  const reorderTodos = useCallback(async (orderedIds: string[]): Promise<boolean> => {
    setError(null)

    // Build reorder request
    const items = orderedIds.map((id, index) => ({ id, sort_order: index }))

    // Optimistic update
    const reordered = orderedIds
      .map(id => todos.find(t => t.id === id))
      .filter((t): t is Todo => t !== undefined)
    setTodos(reordered)

    try {
      await api.put('/api/todos/reorder', { items })
      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reorder todos'
      setError(message)
      // Revert on error
      await fetchTodos()
      return false
    }
  }, [todos, fetchTodos])

  return {
    todos, loading, error, filter, total, hasMore, fromCache,
    setFilter, fetchTodos, loadMore, createTodo,
    updateTodo, deleteTodo, toggleTodo, reorderTodos,
  }
}

/** Recursively find a todo by id in a nested tree */
function findTodoById(todos: Todo[], id: string): Todo | undefined {
  for (const todo of todos) {
    if (todo.id === id) return todo
    if (todo.children) {
      const found = findTodoById(todo.children, id)
      if (found) return found
    }
  }
  return undefined
}
