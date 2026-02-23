import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTodos } from './use-todos'
import { api } from '@/lib/api'
import type { Todo, PaginatedResponse } from '@/lib/types'

vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 })
vi.mocked(api.post).mockResolvedValue({} as Todo)
vi.mocked(api.put).mockResolvedValue({} as Todo)
vi.mocked(api.delete).mockResolvedValue(undefined)

describe('useTodos', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useTodos())

    expect(result.current.todos).toEqual([])
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.filter).toBe('all')
  })

  it('should fetch todos with all filter', async () => {
    const mockTodos: Todo[] = [
      {
        id: '1',
        user_id: 'user1',
        title: 'Test Todo',
        description: null,
        is_completed: false,
        completed_at: null,
        deadline: null,
        parent_id: null,
        note_id: null,
        priority: 0,
        sort_order: 0,
        reminder_at: null,
        reminder_sent: false,
        recurrence_type: null,
        recurrence_interval: null,
        recurrence_days: null,
        recurrence_end_date: null,
        recurrence_parent_id: null,
        created_at: '2026-02-15T00:00:00Z',
        updated_at: '2026-02-15T00:00:00Z',
        tags: [],
      },
    ]

    vi.mocked(api.get).mockResolvedValueOnce({ items: mockTodos, total: 1, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    await act(async () => {
      await result.current.fetchTodos()
    })

    expect(result.current.todos).toEqual(mockTodos)
    expect(api.get).toHaveBeenCalled()
  })

  it('should fetch todos with active filter', async () => {
    const mockTodos: Todo[] = []
    vi.mocked(api.get).mockResolvedValueOnce({ items: mockTodos, total: 0, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    await act(async () => {
      await result.current.fetchTodos('active')
    })

    expect(api.get).toHaveBeenCalled()
  })

  it('should fetch todos with completed filter', async () => {
    const mockTodos: Todo[] = []
    vi.mocked(api.get).mockResolvedValueOnce({ items: mockTodos, total: 0, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    await act(async () => {
      await result.current.fetchTodos('completed')
    })

    expect(api.get).toHaveBeenCalled()
  })

  it('should fetch todos with overdue filter', async () => {
    const mockTodos: Todo[] = []
    vi.mocked(api.get).mockResolvedValueOnce({ items: mockTodos, total: 0, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    await act(async () => {
      await result.current.fetchTodos('overdue')
    })

    expect(api.get).toHaveBeenCalled()
  })

  it('should update filter state', () => {
    const { result } = renderHook(() => useTodos())

    expect(result.current.filter).toBe('all')

    act(() => {
      result.current.setFilter('active')
    })

    expect(result.current.filter).toBe('active')
  })

  it('should handle fetch error', async () => {
    const errorMessage = 'Failed to fetch todos'
    vi.mocked(api.get).mockRejectedValueOnce(new Error(errorMessage))

    const { result } = renderHook(() => useTodos())

    await act(async () => {
      await result.current.fetchTodos()
    })

    expect(result.current.error).toBe(errorMessage)
    expect(result.current.todos).toEqual([])
  })

  it('should create todo', async () => {
    const newTodo: Todo = {
      id: '2',
      user_id: 'user1',
      title: 'New Todo',
      description: 'New description',
      is_completed: false,
      completed_at: null,
      deadline: null,
      parent_id: null,
      note_id: null,
      priority: 1,
      sort_order: 0,
      reminder_at: null,
      reminder_sent: false,
      recurrence_type: null,
      recurrence_interval: null,
      recurrence_days: null,
      recurrence_end_date: null,
      recurrence_parent_id: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
      tags: [],
    }

    vi.mocked(api.post).mockResolvedValueOnce(newTodo)
    vi.mocked(api.get).mockResolvedValueOnce({ items: [newTodo], total: 1, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    let createdTodo: Todo | null = null
    await act(async () => {
      createdTodo = await result.current.createTodo({
        title: 'New Todo',
        description: 'New description',
        priority: 1,
      })
    })

    expect(createdTodo).toEqual(newTodo)
    expect(api.post).toHaveBeenCalledWith('/api/todos', {
      title: 'New Todo',
      description: 'New description',
      priority: 1,
    })
  })

  it('should return null on create failure', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Create failed'))

    const { result } = renderHook(() => useTodos())

    let createdTodo: Todo | null = null
    await act(async () => {
      createdTodo = await result.current.createTodo({ title: 'New Todo' })
    })

    expect(createdTodo).toBeNull()
    expect(result.current.error).toBe('Create failed')
  })

  it('should update todo', async () => {
    const updatedTodo: Todo = {
      id: '1',
      user_id: 'user1',
      title: 'Updated Todo',
      description: null,
      is_completed: false,
      completed_at: null,
      deadline: null,
      parent_id: null,
      note_id: null,
      priority: 0,
      sort_order: 0,
      reminder_at: null,
      reminder_sent: false,
      recurrence_type: null,
      recurrence_interval: null,
      recurrence_days: null,
      recurrence_end_date: null,
      recurrence_parent_id: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
      tags: [],
    }

    vi.mocked(api.put).mockResolvedValueOnce(updatedTodo)
    vi.mocked(api.get).mockResolvedValueOnce({ items: [updatedTodo], total: 1, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    let returnedTodo: Todo | null = null
    await act(async () => {
      returnedTodo = await result.current.updateTodo('1', { title: 'Updated Todo' })
    })

    expect(returnedTodo).toEqual(updatedTodo)
    expect(api.put).toHaveBeenCalledWith('/api/todos/1', { title: 'Updated Todo' })
  })

  it('should return null on update failure', async () => {
    vi.mocked(api.put).mockRejectedValueOnce(new Error('Update failed'))

    const { result } = renderHook(() => useTodos())

    let returnedTodo: Todo | null = null
    await act(async () => {
      returnedTodo = await result.current.updateTodo('1', { title: 'Updated' })
    })

    expect(returnedTodo).toBeNull()
    expect(result.current.error).toBe('Update failed')
  })

  it('should delete todo', async () => {
    vi.mocked(api.delete).mockResolvedValueOnce(undefined)
    vi.mocked(api.get).mockResolvedValueOnce({ items: [], total: 0, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    let success: boolean = false
    await act(async () => {
      success = await result.current.deleteTodo('1')
    })

    expect(success).toBe(true)
    expect(api.delete).toHaveBeenCalledWith('/api/todos/1')
  })

  it('should return false on delete failure', async () => {
    vi.mocked(api.delete).mockRejectedValueOnce(new Error('Delete failed'))

    const { result } = renderHook(() => useTodos())

    let success: boolean = true
    await act(async () => {
      success = await result.current.deleteTodo('1')
    })

    expect(success).toBe(false)
    expect(result.current.error).toBe('Delete failed')
  })

  it('should toggle todo completion status', async () => {
    const incompleteTodo: Todo = {
      id: '1',
      user_id: 'user1',
      title: 'Test Todo',
      description: null,
      is_completed: false,
      completed_at: null,
      deadline: null,
      parent_id: null,
      note_id: null,
      priority: 0,
      sort_order: 0,
      reminder_at: null,
      reminder_sent: false,
      recurrence_type: null,
      recurrence_interval: null,
      recurrence_days: null,
      recurrence_end_date: null,
      recurrence_parent_id: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
      tags: [],
    }

    const completedTodo: Todo = {
      ...incompleteTodo,
      is_completed: true,
      completed_at: '2026-02-15T00:00:00Z',
    }

    vi.mocked(api.get).mockResolvedValueOnce({ items: [incompleteTodo], total: 1, limit: 50, offset: 0 })

    const { result } = renderHook(() => useTodos())

    // Fetch initial todos
    await act(async () => {
      await result.current.fetchTodos()
    })

    // toggleTodo now uses POST /api/todos/{id}/toggle endpoint
    vi.mocked(api.post).mockResolvedValueOnce(completedTodo)
    vi.mocked(api.get).mockResolvedValueOnce({ items: [completedTodo], total: 1, limit: 50, offset: 0 })

    let toggledTodo: Todo | null = null
    await act(async () => {
      toggledTodo = await result.current.toggleTodo('1')
    })

    expect(toggledTodo).not.toBeNull()
    expect(toggledTodo!.is_completed).toBe(true)
  })

  it('should return null when toggling non-existent todo (API error)', async () => {
    const { result } = renderHook(() => useTodos())

    // Mock API error (e.g., 404 not found)
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Todo not found'))

    let toggledTodo: Todo | null = null
    await act(async () => {
      toggledTodo = await result.current.toggleTodo('nonexistent')
    })

    expect(toggledTodo).toBeNull()
    expect(result.current.error).toBe('Todo not found')
  })

  it('should clear error on successful fetch', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Fetch error'))

    const { result } = renderHook(() => useTodos())

    await act(async () => {
      await result.current.fetchTodos()
    })

    expect(result.current.error).toBe('Fetch error')

    vi.clearAllMocks()
    vi.mocked(api.get).mockResolvedValueOnce({ items: [], total: 0, limit: 50, offset: 0 })

    await act(async () => {
      await result.current.fetchTodos()
    })

    expect(result.current.error).toBeNull()
  })
})
