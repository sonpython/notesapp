'use client'

import { useCallback, useEffect, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { markdown } from '@codemirror/lang-markdown'
import { Pin, Archive, Eye, Edit3, Trash2 } from 'lucide-react'
import type { Note } from '@/lib/types'
import { useDebounce } from '@/hooks/use-debounce'
import { useTags } from '@/hooks/use-tags'
import { NotePreview } from '@/components/notes/note-preview'
import { NoteExportMenu } from '@/components/notes/note-export-menu'
import { TagSelector } from '@/components/tags/tag-selector'

interface NoteEditorProps {
  note: Note | null
  onSave: (id: string, data: { title?: string; content?: string; is_pinned?: boolean; is_archived?: boolean }) => void
  onDelete?: (id: string) => void
  onExportAll?: () => Promise<void>
}

/**
 * Full note editor with title input, CodeMirror markdown editor,
 * preview toggle, and action toolbar (pin, archive, delete).
 * Auto-saves changes after 500ms debounce.
 */
export function NoteEditor({ note, onSave, onDelete, onExportAll }: NoteEditorProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [isPreview, setIsPreview] = useState(false)
  const { tags, fetchTags, createTag, addTagToNote, removeTagFromNote } = useTags()

  const debouncedTitle = useDebounce(title, 500)
  const debouncedContent = useDebounce(content, 500)

  // Fetch tags on mount
  useEffect(() => {
    fetchTags()
  }, [fetchTags])

  // Sync local state when selected note changes
  useEffect(() => {
    if (note) {
      setTitle(note.title)
      setContent(note.content)
      setIsPreview(false)
    }
  }, [note?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-save on debounced title changes
  useEffect(() => {
    if (!note || debouncedTitle === note.title) return
    onSave(note.id, { title: debouncedTitle })
  }, [debouncedTitle]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-save on debounced content changes
  useEffect(() => {
    if (!note || debouncedContent === note.content) return
    onSave(note.id, { content: debouncedContent })
  }, [debouncedContent]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleTogglePin = useCallback(() => {
    if (note) onSave(note.id, { is_pinned: !note.is_pinned })
  }, [note, onSave])

  const handleToggleArchive = useCallback(() => {
    if (note) onSave(note.id, { is_archived: !note.is_archived })
  }, [note, onSave])

  const handleDelete = useCallback(() => {
    if (note && onDelete) onDelete(note.id)
  }, [note, onDelete])

  const handleAddTag = useCallback(async (tagId: string) => {
    if (!note) return
    await addTagToNote(note.id, [tagId])
    // Refresh note by triggering parent refetch
    window.location.reload()
  }, [note, addTagToNote])

  const handleRemoveTag = useCallback(async (tagId: string) => {
    if (!note) return
    await removeTagFromNote(note.id, tagId)
    // Refresh note by triggering parent refetch
    window.location.reload()
  }, [note, removeTagFromNote])

  const handleCreateTag = useCallback(async (name: string, color: string) => {
    const created = await createTag({ name, color })
    if (created) {
      await fetchTags()
    }
    return created
  }, [createTag, fetchTags])

  // Empty state placeholder
  if (!note) {
    return (
      <div className="flex items-center justify-center h-full text-muted">
        <p className="text-lg">Select a note to start editing</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border shrink-0">
        <div className="flex items-center gap-1">
          <ToolbarButton
            onClick={handleTogglePin}
            active={note.is_pinned}
            title={note.is_pinned ? 'Unpin' : 'Pin'}
          >
            <Pin className="w-4 h-4" />
          </ToolbarButton>
          <ToolbarButton
            onClick={handleToggleArchive}
            active={note.is_archived}
            title={note.is_archived ? 'Unarchive' : 'Archive'}
          >
            <Archive className="w-4 h-4" />
          </ToolbarButton>
          {onDelete && (
            <ToolbarButton onClick={handleDelete} title="Delete">
              <Trash2 className="w-4 h-4" />
            </ToolbarButton>
          )}
        </div>
        <div className="flex items-center gap-1">
          <NoteExportMenu note={note} onExportAll={onExportAll} />
          <ToolbarButton
            onClick={() => setIsPreview(prev => !prev)}
            active={isPreview}
            title={isPreview ? 'Edit' : 'Preview'}
          >
            {isPreview ? <Edit3 className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </ToolbarButton>
        </div>
      </div>

      {/* Tags selector */}
      <div className="px-4 py-2 border-b border-border">
        <TagSelector
          selectedTags={note.tags || []}
          allTags={tags}
          onAdd={handleAddTag}
          onRemove={handleRemoveTag}
          onCreate={handleCreateTag}
        />
      </div>

      {/* Title input */}
      <input
        type="text"
        value={title}
        onChange={e => setTitle(e.target.value)}
        placeholder="Untitled"
        className="w-full px-4 py-3 text-2xl font-bold bg-transparent border-none outline-none text-foreground placeholder:text-muted/50"
      />

      {/* Editor or Preview */}
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {isPreview ? (
          <NotePreview content={content} />
        ) : (
          <CodeMirror
            value={content}
            onChange={val => setContent(val)}
            extensions={[markdown()]}
            theme="dark"
            placeholder="Start writing..."
            className="min-h-full text-base"
            basicSetup={{
              lineNumbers: false,
              foldGutter: false,
              highlightActiveLine: false,
            }}
          />
        )}
      </div>
    </div>
  )
}

/** Small toolbar icon button with active state highlight. */
function ToolbarButton({
  onClick,
  active = false,
  title,
  children,
}: {
  onClick: () => void
  active?: boolean
  title: string
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`p-1.5 rounded-md transition-colors cursor-pointer ${
        active
          ? 'text-accent bg-accent/10'
          : 'text-muted hover:text-foreground hover:bg-sidebar'
      }`}
    >
      {children}
    </button>
  )
}
