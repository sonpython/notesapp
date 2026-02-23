'use client'

import { useCallback } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import type { Todo } from '@/lib/types'
import { SortableTodoItem } from './sortable-todo-item'

interface TodoListProps {
  todos: Todo[]
  onToggle: (id: string) => void
  onUpdate: (id: string, data: Record<string, unknown>) => void
  onDelete: (id: string) => void
  onReorder?: (orderedIds: string[]) => void
}

/**
 * Renders a sortable list of TodoItem components with drag-and-drop.
 * Each item handles its own children recursively.
 */
export function TodoList({ todos, onToggle, onUpdate, onDelete, onReorder }: TodoListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id || !onReorder) return

    const oldIndex = todos.findIndex(t => t.id === active.id)
    const newIndex = todos.findIndex(t => t.id === over.id)
    if (oldIndex === -1 || newIndex === -1) return

    // Create new order
    const newOrder = [...todos]
    const [removed] = newOrder.splice(oldIndex, 1)
    newOrder.splice(newIndex, 0, removed)

    onReorder(newOrder.map(t => t.id))
  }, [todos, onReorder])

  if (todos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted">
        <p className="text-sm">No todos yet. Create one above.</p>
      </div>
    )
  }

  // Only root-level (incomplete) todos are sortable
  const sortableIds = todos.filter(t => !t.is_completed).map(t => t.id)

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
        <div className="flex flex-col divide-y divide-border">
          {todos.map((todo) => (
            <SortableTodoItem
              key={todo.id}
              todo={todo}
              onToggle={onToggle}
              onUpdate={onUpdate}
              onDelete={onDelete}
              depth={0}
              isDraggable={!todo.is_completed}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}
