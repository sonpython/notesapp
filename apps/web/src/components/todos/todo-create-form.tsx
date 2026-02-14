'use client'

import { useState, type FormEvent } from 'react'
import { Plus, Calendar, Bell } from 'lucide-react'
import type { Todo } from '@/lib/types'

interface TodoCreateFormProps {
  onCreated: (todo: Todo) => void
  parentId?: string
}

/**
 * Compact inline form for creating new todos or subtasks.
 * Includes title, priority, deadline, and reminder fields.
 */
export function TodoCreateForm({ onCreated, parentId }: TodoCreateFormProps) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState(0)
  const [deadline, setDeadline] = useState('')
  const [reminderAt, setReminderAt] = useState('')
  const [showExtras, setShowExtras] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed || submitting) return

    setSubmitting(true)
    try {
      // Build payload, omitting empty optional fields
      const payload: Record<string, unknown> = {
        title: trimmed,
        priority,
      }
      if (deadline) payload.deadline = deadline
      if (reminderAt) payload.reminder_at = reminderAt
      if (parentId) payload.parent_id = parentId

      // onCreated handles the API call via the hook
      onCreated(payload as unknown as Todo)

      // Reset form
      setTitle('')
      setPriority(0)
      setDeadline('')
      setReminderAt('')
      setShowExtras(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={!title.trim() || submitting}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md
            bg-accent text-black transition-opacity hover:opacity-90
            disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Add todo"
        >
          <Plus size={16} />
        </button>

        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={parentId ? 'Add subtask...' : 'New todo...'}
          className="h-8 flex-1 rounded-md border border-border bg-background px-3
            text-sm text-foreground placeholder:text-muted
            focus:outline-none focus:ring-1 focus:ring-accent"
        />

        {/* Priority selector */}
        <select
          value={priority}
          onChange={(e) => setPriority(Number(e.target.value))}
          className="h-8 rounded-md border border-border bg-background px-2
            text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          aria-label="Priority"
        >
          <option value={0}>No priority</option>
          <option value={1}>Low</option>
          <option value={2}>Medium</option>
          <option value={3}>High</option>
        </select>

        {/* Toggle extra fields */}
        <button
          type="button"
          onClick={() => setShowExtras(!showExtras)}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md
            border border-border text-muted transition-colors hover:text-foreground"
          aria-label="More options"
        >
          <Calendar size={14} />
        </button>
      </div>

      {showExtras && (
        <div className="ml-10 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-muted">
            <Calendar size={12} />
            <input
              type="datetime-local"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="h-7 rounded border border-border bg-background px-2
                text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </label>

          <label className="flex items-center gap-1.5 text-xs text-muted">
            <Bell size={12} />
            <input
              type="datetime-local"
              value={reminderAt}
              onChange={(e) => setReminderAt(e.target.value)}
              className="h-7 rounded border border-border bg-background px-2
                text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </label>
        </div>
      )}
    </form>
  )
}
