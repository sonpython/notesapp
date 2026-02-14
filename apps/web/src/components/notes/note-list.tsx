'use client'

import { Pin } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Note } from '@/lib/types'

interface NoteListProps {
  notes: Note[]
  selectedId: string | null
  onSelect: (id: string) => void
}

/** Extracts the first non-empty line of content as a preview snippet. */
function getContentPreview(content: string): string {
  const firstLine = content
    .split('\n')
    .map(line => line.replace(/^#+\s*/, '').trim())
    .find(line => line.length > 0)
  if (!firstLine) return 'No additional text'
  return firstLine.length > 80 ? firstLine.slice(0, 80) + '...' : firstLine
}

/** Formats a date string as a relative time (e.g. "2 hours ago"). */
function formatDate(dateString: string): string {
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true })
  } catch {
    return ''
  }
}

/**
 * Scrollable list of note items sorted with pinned notes first.
 * Each item shows title, content preview, and relative date.
 */
export function NoteList({ notes, selectedId, onSelect }: NoteListProps) {
  // Sort: pinned first, then by updated_at descending
  const sortedNotes = [...notes].sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1
    if (!a.is_pinned && b.is_pinned) return 1
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })

  if (sortedNotes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted text-sm">
        No notes yet
      </div>
    )
  }

  return (
    <div className="overflow-y-auto h-full">
      {sortedNotes.map(note => {
        const isSelected = note.id === selectedId
        return (
          <button
            key={note.id}
            onClick={() => onSelect(note.id)}
            className={`
              w-full text-left px-4 py-3 border-b border-border
              transition-colors cursor-pointer
              ${isSelected
                ? 'bg-accent/10 border-l-2 border-l-accent'
                : 'hover:bg-sidebar border-l-2 border-l-transparent'
              }
            `}
          >
            <div className="flex items-center gap-1.5 mb-1">
              {note.is_pinned && (
                <Pin className="w-3 h-3 text-accent shrink-0" />
              )}
              <span className="font-medium text-sm text-foreground truncate">
                {note.title || 'Untitled'}
              </span>
            </div>
            <p className="text-xs text-muted truncate mb-1">
              {getContentPreview(note.content)}
            </p>
            <span className="text-[11px] text-muted/70">
              {formatDate(note.updated_at)}
            </span>
          </button>
        )
      })}
    </div>
  )
}
