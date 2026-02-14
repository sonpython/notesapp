'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Plus, Search } from 'lucide-react'
import { useNotes } from '@/hooks/use-notes'
import { useDebounce } from '@/hooks/use-debounce'
import { NoteList } from '@/components/notes/note-list'
import { NoteEditor } from '@/components/notes/note-editor'

/**
 * Notes page with a 2-column layout: note list (left) and editor (right).
 * Supports creating, selecting, searching, and editing notes.
 */
export default function NotesPage() {
  const searchParams = useSearchParams()
  const { notes, loading, fetchNotes, createNote, updateNote, deleteNote, moveNoteToFolder } = useNotes()
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const folderId = searchParams.get('folder') ?? undefined
  const debouncedSearch = useDebounce(searchQuery, 300)

  // Fetch notes on mount and when folder or debounced search changes
  useEffect(() => {
    fetchNotes(folderId, debouncedSearch || undefined)
  }, [fetchNotes, folderId, debouncedSearch])

  // Find the currently selected note
  const selectedNote = useMemo(
    () => notes.find(n => n.id === selectedNoteId) ?? null,
    [notes, selectedNoteId]
  )

  // Create a new note and select it
  const handleCreateNote = useCallback(async () => {
    try {
      const newNote = await createNote({ title: '', content: '' })
      setSelectedNoteId(newNote.id)
    } catch {
      // Error handled inside useNotes hook
    }
  }, [createNote])

  // Save handler for the editor (title, content, pin, archive)
  const handleSave = useCallback(
    (id: string, data: { title?: string; content?: string; is_pinned?: boolean; is_archived?: boolean }) => {
      updateNote(id, data)
    },
    [updateNote]
  )

  // Delete handler clears selection if active note is deleted
  const handleDelete = useCallback(
    async (id: string) => {
      await deleteNote(id)
      if (selectedNoteId === id) setSelectedNoteId(null)
    },
    [deleteNote, selectedNoteId]
  )

  // Move note to folder handler
  const handleMoveNote = useCallback(
    async (noteId: string, targetFolderId: string | null) => {
      await moveNoteToFolder(noteId, targetFolderId)
      // Refresh notes to update the view
      await fetchNotes(folderId, debouncedSearch || undefined)
    },
    [moveNoteToFolder, folderId, debouncedSearch, fetchNotes]
  )

  return (
    <div className="flex h-screen bg-background">
      {/* Left panel: search, new note, note list */}
      <div className="w-72 shrink-0 border-r border-border flex flex-col bg-sidebar">
        {/* Header with search and add button */}
        <div className="p-3 border-b border-border space-y-2">
          <div className="flex items-center justify-between">
            <h1 className="text-sm font-semibold text-foreground">Notes</h1>
            <button
              onClick={handleCreateNote}
              title="New Note"
              className="p-1.5 rounded-md text-muted hover:text-foreground hover:bg-background transition-colors cursor-pointer"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search notes..."
              className="w-full pl-8 pr-3 py-1.5 text-sm bg-background border border-border rounded-md outline-none text-foreground placeholder:text-muted/60 focus:border-accent/50 transition-colors"
            />
          </div>
        </div>

        {/* Note list */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full text-muted text-sm">
              Loading...
            </div>
          ) : (
            <NoteList
              notes={notes}
              selectedId={selectedNoteId}
              onSelect={setSelectedNoteId}
              onMoveNote={handleMoveNote}
            />
          )}
        </div>
      </div>

      {/* Right panel: editor */}
      <div className="flex-1 min-w-0">
        <NoteEditor
          note={selectedNote}
          onSave={handleSave}
          onDelete={handleDelete}
        />
      </div>
    </div>
  )
}
