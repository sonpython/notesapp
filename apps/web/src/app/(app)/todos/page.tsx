'use client'

import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { Search, AlertCircle } from 'lucide-react'
import { useTodos, type TodoFilter } from '@/hooks/use-todos'
import { TodoList } from '@/components/todos/todo-list'
import { TodoCreateForm } from '@/components/todos/todo-create-form'
import type { Todo } from '@/lib/types'

const FILTER_TABS: { label: string; value: TodoFilter }[] = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Completed', value: 'completed' },
  { label: 'Overdue', value: 'overdue' },
]

/**
 * Full-width todo list page with filter tabs, search, and inline creation.
 */
export default function TodosPage() {
  const searchParams = useSearchParams()
  const {
    todos, loading, error, filter,
    setFilter, fetchTodos, createTodo,
    updateTodo, deleteTodo, toggleTodo,
  } = useTodos()

  const [search, setSearch] = useState('')
  const tagIdsParam = searchParams.get('tags')
  const tagIds = tagIdsParam ? tagIdsParam.split(',') : undefined

  // Fetch todos on mount and when filter or tags change
  useEffect(() => {
    fetchTodos(filter, tagIds)
  }, [filter, tagIds, fetchTodos])

  const handleFilterChange = (newFilter: TodoFilter) => {
    setFilter(newFilter)
  }

  const handleCreated = useCallback(async (payload: Todo) => {
    // payload is raw form data cast as Todo; pass to createTodo
    await createTodo(payload as unknown as Parameters<typeof createTodo>[0])
  }, [createTodo])

  const handleUpdate = useCallback(async (id: string, data: Record<string, unknown>) => {
    // Special case: subtask creation forwarded from TodoItem
    if (id === '__create__') {
      await createTodo(data as unknown as Parameters<typeof createTodo>[0])
      return
    }
    await updateTodo(id, data)
  }, [updateTodo, createTodo])

  // Client-side search filtering
  const filtered = search.trim()
    ? todos.filter((t) => t.title.toLowerCase().includes(search.toLowerCase()))
    : todos

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      {/* Header */}
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Todos</h1>

      {/* Search input */}
      <div className="relative mt-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search todos..."
          className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3
            text-sm text-foreground placeholder:text-muted
            focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Filter tabs */}
      <div className="mt-4 flex gap-1 border-b border-border">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleFilterChange(tab.value)}
            className={`px-3 py-2 text-sm font-medium transition-colors
              ${filter === tab.value
                ? 'border-b-2 border-accent text-foreground'
                : 'text-muted hover:text-foreground'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Create form */}
      <div className="mt-4">
        <TodoCreateForm onCreated={handleCreated} />
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-500">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="mt-8 flex justify-center text-sm text-muted">Loading...</div>
      )}

      {/* Todo list */}
      {!loading && (
        <div className="mt-4">
          <TodoList
            todos={filtered}
            onToggle={toggleTodo}
            onUpdate={handleUpdate}
            onDelete={deleteTodo}
          />
        </div>
      )}
    </div>
  )
}
