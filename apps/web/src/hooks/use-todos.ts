'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Todo, PaginatedResponse } from '@/lib/types'

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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch todos'
      setError(message)
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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load more todos'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [loading, hasMore, offset, limit, filter, currentTagIds])

  const createTodo = useCallback(async (data: CreateTodoData): Promise<Todo | null> => {
    setError(null)
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
    const target = findTodoById(todos, id)
    if (!target) return null
    return updateTodo(id, { is_completed: !target.is_completed })
  }, [todos, updateTodo])

  return {
    todos, loading, error, filter, total, hasMore,
    setFilter, fetchTodos, loadMore, createTodo,
    updateTodo, deleteTodo, toggleTodo,
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
