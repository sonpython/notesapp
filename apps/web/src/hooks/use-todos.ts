'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Todo } from '@/lib/types'

/** Filter type for todo list views */
export type TodoFilter = 'all' | 'active' | 'completed' | 'overdue'

interface CreateTodoData {
  title: string
  description?: string
  priority?: number
  deadline?: string
  parent_id?: string
  reminder_at?: string
}

interface UpdateTodoData {
  title?: string
  description?: string
  priority?: number
  deadline?: string
  is_completed?: boolean
  reminder_at?: string
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

  const fetchTodos = useCallback(async (activeFilter?: TodoFilter) => {
    setLoading(true)
    setError(null)
    try {
      const filterParam = activeFilter || filter
      const query = filterParam !== 'all' ? `?filter=${filterParam}` : ''
      const data = await api.get<Todo[]>(`/api/todos${query}`)
      setTodos(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch todos'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [filter])

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
    todos, loading, error, filter,
    setFilter, fetchTodos, createTodo,
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
