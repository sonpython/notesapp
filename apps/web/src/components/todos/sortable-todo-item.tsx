'use client'

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'
import type { Todo } from '@/lib/types'
import { TodoItem } from './todo-item'

interface SortableTodoItemProps {
  todo: Todo
  onToggle: (id: string) => void
  onUpdate: (id: string, data: Record<string, unknown>) => void
  onDelete: (id: string) => void
  depth: number
  isDraggable?: boolean
}

/**
 * Wrapper component that makes TodoItem sortable via drag-and-drop.
 * Only root-level incomplete todos are draggable.
 */
export function SortableTodoItem({
  todo,
  onToggle,
  onUpdate,
  onDelete,
  depth,
  isDraggable = true,
}: SortableTodoItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: todo.id, disabled: !isDraggable })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="relative">
      {/* Drag handle - only show for root-level incomplete todos */}
      {isDraggable && depth === 0 && (
        <button
          {...attributes}
          {...listeners}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 flex h-8 w-6 cursor-grab
            items-center justify-center text-muted opacity-0 transition-opacity
            hover:text-foreground group-hover:opacity-100 active:cursor-grabbing
            touch-none"
          aria-label="Drag to reorder"
        >
          <GripVertical size={14} />
        </button>
      )}
      <div className={isDraggable && depth === 0 ? 'pl-6' : ''}>
        <TodoItem
          todo={todo}
          onToggle={onToggle}
          onUpdate={onUpdate}
          onDelete={onDelete}
          depth={depth}
        />
      </div>
    </div>
  )
}
