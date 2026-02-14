'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Plus, Search } from 'lucide-react'
import { useNotes } from '@/hooks/use-notes'
import { createClient } from '@/lib/supabase-browser'
import { useDebounce } from '@/hooks/use-debounce'
import { NoteList } from '@/components/notes/note-list'
import { NoteEditor } from '@/components/notes/note-editor'
import { ResizableDivider } from '@/components/ui/resizable-divider'

const NOTE_LIST_WIDTH_KEY = 'notesapp-note-list-width'
const DEFAULT_NOTE_LIST_WIDTH = 288 // 72 * 4 = 288px (w-72)
const MIN_NOTE_LIST_WIDTH = 250
const MAX_NOTE_LIST_WIDTH = 500

/**
 * Notes page with a 2-column layout: note list (left) and editor (right).
 * Supports creating, selecting, searching, and editing notes.
 * Panels are resizable via drag divider.
 */
export default function NotesPage() {
  const searchParams = useSearchParams()
  const { notes, loading, fetchNotes, createNote, updateNote, deleteNote, moveNoteToFolder } = useNotes()
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [noteListWidth, setNoteListWidth] = useState(DEFAULT_NOTE_LIST_WIDTH)
  const [mounted, setMounted] = useState(false)

  // Load width from localStorage after mount to avoid hydration mismatch
  useEffect(() => {
    const saved = localStorage.getItem(NOTE_LIST_WIDTH_KEY)
    if (saved) setNoteListWidth(parseInt(saved, 10))
    setMounted(true)
  }, [])

  const folderId = searchParams.get('folder') ?? undefined
  const tagIdsParam = searchParams.get('tags')
  const tagIds = useMemo(
    () => (tagIdsParam ? tagIdsParam.split(',') : undefined),
    [tagIdsParam]
  )
  const debouncedSearch = useDebounce(searchQuery, 300)

  // Fetch notes on mount and when folder, tags, or debounced search changes
  useEffect(() => {
    fetchNotes(folderId, debouncedSearch || undefined, tagIds)
  }, [fetchNotes, folderId, debouncedSearch, tagIds])

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

  // Handle note list resize
  const handleNoteListResize = useCallback((newWidth: number) => {
    const clampedWidth = Math.max(MIN_NOTE_LIST_WIDTH, Math.min(MAX_NOTE_LIST_WIDTH, newWidth))
    setNoteListWidth(clampedWidth)
    localStorage.setItem(NOTE_LIST_WIDTH_KEY, clampedWidth.toString())
  }, [])

  // Handle export all notes as ZIP
  const handleExportAll = useCallback(async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const headers: HeadersInit = {}
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/notes/export/zip`, { headers })
      if (!response.ok) throw new Error('Export failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'notes_export.zip'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Bulk export failed:', error)
      throw error
    }
  }, [])

  return (
    <div className="flex h-screen bg-background">
      {/* Left panel: search, new note, note list */}
      <div
        className="shrink-0 flex flex-col bg-sidebar"
        style={{ width: noteListWidth }}
      >
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

      {/* Resizable divider */}
      <ResizableDivider onResize={handleNoteListResize} />

      {/* Right panel: editor */}
      <div className="flex-1 min-w-0">
        <NoteEditor
          note={selectedNote}
          onSave={handleSave}
          onDelete={handleDelete}
          onExportAll={handleExportAll}
        />
      </div>
    </div>
  )
}
