'use client'

import type { Todo } from '@/lib/types'
import { TodoItem } from './todo-item'

interface TodoListProps {
  todos: Todo[]
  onToggle: (id: string) => void
  onUpdate: (id: string, data: Record<string, unknown>) => void
  onDelete: (id: string) => void
}

/**
 * Renders a flat list of TodoItem components.
 * Each item handles its own children recursively.
 */
export function TodoList({ todos, onToggle, onUpdate, onDelete }: TodoListProps) {
  if (todos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted">
        <p className="text-sm">No todos yet. Create one above.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col divide-y divide-border">
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={onToggle}
          onUpdate={onUpdate}
          onDelete={onDelete}
          depth={0}
        />
      ))}
    </div>
  )
}
