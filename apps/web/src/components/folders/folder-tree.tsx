'use client'

import { useState, useRef, useEffect } from 'react'
import { FolderIcon, Plus, FileText } from 'lucide-react'
import { FolderTreeItem } from './folder-tree-item'
import type { Folder } from '@/lib/types'

interface FolderTreeProps {
  folders: Folder[]
  selectedFolderId: string | null
  onSelectFolder: (id: string | null) => void
  onCreateFolder: (name: string, parentId?: string) => Promise<Folder>
  onRenameFolder: (id: string, name: string) => Promise<Folder>
  onDeleteFolder: (id: string) => Promise<void>
  onMoveNote?: (noteId: string, folderId: string | null) => Promise<void>
}

/**
 * Folder tree container with "All Notes" option, root folder creation,
 * and recursive folder items. Shows empty state when no folders exist.
 */
export function FolderTree({
  folders,
  selectedFolderId,
  onSelectFolder,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
  onMoveNote,
}: FolderTreeProps) {
  const [isCreatingRoot, setIsCreatingRoot] = useState(false)
  const [newRootName, setNewRootName] = useState('')
  const newRootInputRef = useRef<HTMLInputElement>(null)

  // Focus input when creating root folder
  useEffect(() => {
    if (isCreatingRoot && newRootInputRef.current) {
      newRootInputRef.current.focus()
    }
  }, [isCreatingRoot])

  const handleCreateRootSubmit = async () => {
    const trimmed = newRootName.trim()
    if (trimmed) {
      try {
        await onCreateFolder(trimmed)
        setNewRootName('')
        setIsCreatingRoot(false)
      } catch {
        // Error handled in parent
      }
    }
  }

  const handleCreateRootKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCreateRootSubmit()
    } else if (e.key === 'Escape') {
      setNewRootName('')
      setIsCreatingRoot(false)
    }
  }

  const isEmpty = folders.length === 0 && !isCreatingRoot

  return (
    <div className="space-y-0.5">
      {/* "All Notes" item */}
      <button
        type="button"
        onClick={() => onSelectFolder(null)}
        className={`w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors text-left ${
          selectedFolderId === null
            ? 'bg-zinc-700/60 text-white'
            : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
        }`}
      >
        <FileText className="h-4 w-4 shrink-0" />
        All Notes
      </button>

      {/* Empty state */}
      {isEmpty && (
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <FolderIcon className="h-8 w-8 text-zinc-700" />
          <p className="text-xs text-zinc-600">No folders yet</p>
          <button
            type="button"
            onClick={() => setIsCreatingRoot(true)}
            className="flex items-center gap-1.5 rounded-md bg-zinc-800 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-zinc-300"
          >
            <Plus className="h-3 w-3" />
            New Folder
          </button>
        </div>
      )}

      {/* New root folder input */}
      {isCreatingRoot && (
        <div className="flex items-center gap-1.5 px-3 py-1.5">
          <FolderIcon className="h-4 w-4 shrink-0 text-yellow-500" />
          <input
            ref={newRootInputRef}
            type="text"
            value={newRootName}
            onChange={(e) => setNewRootName(e.target.value)}
            onBlur={handleCreateRootSubmit}
            onKeyDown={handleCreateRootKeyDown}
            placeholder="Folder name"
            className="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5 text-sm text-white outline-none focus:border-yellow-500 placeholder:text-zinc-500"
          />
        </div>
      )}

      {/* Folder tree */}
      {folders.map((folder) => (
        <FolderTreeItem
          key={folder.id}
          folder={folder}
          depth={0}
          selectedFolderId={selectedFolderId}
          onSelect={onSelectFolder}
          onRename={onRenameFolder}
          onDelete={onDeleteFolder}
          onCreate={onCreateFolder}
          onMoveNote={onMoveNote}
        />
      ))}
    </div>
  )
}
