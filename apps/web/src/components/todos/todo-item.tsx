'use client'

import { useState } from 'react'
import {
  Check, Circle, Trash2, Bell,
  ChevronRight, ChevronDown, Plus, Calendar, AlertCircle,
} from 'lucide-react'
import { format, isPast } from 'date-fns'
import type { Todo } from '@/lib/types'
import { TodoCreateForm } from './todo-create-form'

interface TodoItemProps {
  todo: Todo
  onToggle: (id: string) => void
  onUpdate: (id: string, data: Record<string, unknown>) => void
  onDelete: (id: string) => void
  depth: number
}

/** Color mapping for priority dot: 1=blue, 2=yellow, 3=red */
const PRIORITY_COLORS: Record<number, string> = {
  1: 'bg-blue-500',
  2: 'bg-yellow-500',
  3: 'bg-red-500',
}

/**
 * Single todo row with checkbox, inline edit, priority dot,
 * deadline, reminder, expand/collapse children, and subtask creation.
 */
export function TodoItem({ todo, onToggle, onUpdate, onDelete, depth }: TodoItemProps) {
  const [expanded, setExpanded] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(todo.title)
  const [showSubtaskForm, setShowSubtaskForm] = useState(false)

  const hasChildren = todo.children && todo.children.length > 0
  const isOverdue = todo.deadline && !todo.is_completed && isPast(new Date(todo.deadline))

  const handleDoubleClick = () => {
    setEditing(true)
    setEditTitle(todo.title)
  }

  const commitEdit = () => {
    const trimmed = editTitle.trim()
    if (trimmed && trimmed !== todo.title) {
      onUpdate(todo.id, { title: trimmed })
    }
    setEditing(false)
  }

  const handleSubtaskCreated = (data: Todo) => {
    // data here is the raw payload from the form; parent hook handles API
    onUpdate('__create__', { ...(data as unknown as Record<string, unknown>), parent_id: todo.id })
    setShowSubtaskForm(false)
  }

  return (
    <div style={{ paddingLeft: depth * 24 }}>
      {/* Main row */}
      <div className="group flex items-center gap-2 px-2 py-2 transition-colors hover:bg-sidebar">
        {/* Expand/collapse toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex h-5 w-5 shrink-0 items-center justify-center text-muted"
          aria-label={expanded ? 'Collapse' : 'Expand'}
        >
          {hasChildren ? (
            expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
          ) : (
            <span className="w-3.5" />
          )}
        </button>

        {/* Completion checkbox */}
        <button
          onClick={() => onToggle(todo.id)}
          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full
            border transition-colors
            ${todo.is_completed
              ? 'border-accent bg-accent text-black'
              : 'border-muted text-transparent hover:border-foreground'
            }`}
          aria-label={todo.is_completed ? 'Mark incomplete' : 'Mark complete'}
        >
          {todo.is_completed ? <Check size={12} /> : <Circle size={12} />}
        </button>

        {/* Priority dot */}
        {todo.priority > 0 && (
          <span
            className={`h-2 w-2 shrink-0 rounded-full ${PRIORITY_COLORS[todo.priority] || ''}`}
            title={`Priority ${todo.priority}`}
          />
        )}

        {/* Title (editable on double-click) */}
        {editing ? (
          <input
            autoFocus
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitEdit()
              if (e.key === 'Escape') setEditing(false)
            }}
            className="min-w-0 flex-1 rounded border border-accent bg-background px-2 py-0.5
              text-sm text-foreground outline-none"
          />
        ) : (
          <span
            onDoubleClick={handleDoubleClick}
            className={`min-w-0 flex-1 cursor-default select-none truncate text-sm
              ${todo.is_completed ? 'text-muted line-through' : 'text-foreground'}`}
          >
            {todo.title}
          </span>
        )}

        {/* Reminder indicator */}
        {todo.reminder_at && (
          <span title="Reminder set"><Bell size={14} className="shrink-0 text-accent" /></span>
        )}

        {/* Deadline */}
        {todo.deadline && (
          <span
            className={`flex shrink-0 items-center gap-1 text-xs
              ${isOverdue ? 'text-red-500' : 'text-muted'}`}
          >
            {isOverdue && <AlertCircle size={12} />}
            <Calendar size={12} />
            {format(new Date(todo.deadline), 'MMM d')}
          </span>
        )}

        {/* Add subtask button */}
        <button
          onClick={() => setShowSubtaskForm(!showSubtaskForm)}
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-muted
            opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
          aria-label="Add subtask"
        >
          <Plus size={14} />
        </button>

        {/* Delete button (visible on hover) */}
        <button
          onClick={() => onDelete(todo.id)}
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-muted
            opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
          aria-label="Delete todo"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* Subtask creation form */}
      {showSubtaskForm && (
        <div style={{ paddingLeft: (depth + 1) * 24 }} className="px-2 pb-2">
          <TodoCreateForm onCreated={handleSubtaskCreated} parentId={todo.id} />
        </div>
      )}

      {/* Recursive children */}
      {expanded && hasChildren && todo.children!.map((child) => (
        <TodoItem
          key={child.id}
          todo={child}
          onToggle={onToggle}
          onUpdate={onUpdate}
          onDelete={onDelete}
          depth={depth + 1}
        />
      ))}
    </div>
  )
}
