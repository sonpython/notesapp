'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronRight, ChevronDown, FolderIcon, FolderOpen } from 'lucide-react'
import type { Folder } from '@/lib/types'
import { FolderContextMenu, FolderMenuTrigger } from './folder-context-menu'

interface FolderTreeItemProps {
  folder: Folder
  depth: number
  selectedFolderId: string | null
  onSelect: (id: string) => void
  onRename: (id: string, name: string) => Promise<Folder>
  onDelete: (id: string) => Promise<void>
  onCreate: (name: string, parentId: string) => Promise<Folder>
}

/** Hook for managing folder rename state and actions */
function useRename(folderId: string, initialName: string, onRename: (id: string, name: string) => Promise<Folder>) {
  const [isRenaming, setIsRenaming] = useState(false)
  const [name, setName] = useState(initialName)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isRenaming && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isRenaming])

  const submit = async () => {
    const trimmed = name.trim()
    if (trimmed && trimmed !== initialName) {
      try {
        await onRename(folderId, trimmed)
      } catch {
        setName(initialName)
      }
    }
    setIsRenaming(false)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') submit()
    else if (e.key === 'Escape') {
      setName(initialName)
      setIsRenaming(false)
    }
  }

  return { isRenaming, name, inputRef, setName, setIsRenaming, submit, onKeyDown }
}

/** Hook for creating child folder */
function useCreateChild(parentId: string, onCreate: (name: string, parentId: string) => Promise<Folder>) {
  const [isCreating, setIsCreating] = useState(false)
  const [name, setName] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isCreating && inputRef.current) inputRef.current.focus()
  }, [isCreating])

  const submit = async () => {
    const trimmed = name.trim()
    if (trimmed) {
      try {
        await onCreate(trimmed, parentId)
        setName('')
        setIsCreating(false)
        return true
      } catch {
        return false
      }
    }
    return false
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') submit()
    else if (e.key === 'Escape') {
      setName('')
      setIsCreating(false)
    }
  }

  return { isCreating, name, inputRef, setName, setIsCreating, submit, onKeyDown }
}

/**
 * Recursive folder tree item with expand/collapse, inline rename,
 * context menu (rename, new subfolder, delete), and nested children.
 */
export function FolderTreeItem({
  folder,
  depth,
  selectedFolderId,
  onSelect,
  onRename,
  onDelete,
  onCreate,
}: FolderTreeItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  const rename = useRename(folder.id, folder.name, onRename)
  const createChild = useCreateChild(folder.id, onCreate)

  const hasChildren = folder.children && folder.children.length > 0
  const isSelected = folder.id === selectedFolderId
  const paddingLeft = 12 + depth * 16

  const handleDelete = async () => {
    if (window.confirm(`Delete "${folder.name}" and all its subfolders and notes?`)) {
      await onDelete(folder.id)
    }
  }

  const handleCreateChild = async () => {
    const success = await createChild.submit()
    if (success) setIsExpanded(true)
  }

  return (
    <div>
      {/* Folder row */}
      <div
        style={{ paddingLeft: `${paddingLeft}px` }}
        className={`group flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors cursor-pointer ${
          isSelected ? 'bg-zinc-700/60 text-white' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
        }`}
        onClick={() => onSelect(folder.id)}
      >
        {hasChildren && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded) }}
            className="shrink-0 p-0.5 rounded hover:bg-zinc-700/50"
          >
            {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        )}

        <span title={folder.name}>
          {isExpanded && hasChildren ? (
            <FolderOpen className="h-4 w-4 shrink-0 text-yellow-500" />
          ) : (
            <FolderIcon className="h-4 w-4 shrink-0 text-yellow-500" />
          )}
        </span>

        {rename.isRenaming ? (
          <input
            ref={rename.inputRef}
            type="text"
            value={rename.name}
            onChange={(e) => rename.setName(e.target.value)}
            onBlur={rename.submit}
            onKeyDown={rename.onKeyDown}
            onClick={(e) => e.stopPropagation()}
            className="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5 text-sm text-white outline-none focus:border-yellow-500"
          />
        ) : (
          <span className="flex-1 truncate">{folder.name}</span>
        )}

        <div className="relative">
          <FolderMenuTrigger onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu) }} />
          <FolderContextMenu
            show={showMenu}
            onClose={() => setShowMenu(false)}
            onRename={() => rename.setIsRenaming(true)}
            onNewSubfolder={() => { createChild.setIsCreating(true); setIsExpanded(true) }}
            onDelete={handleDelete}
          />
        </div>
      </div>

      {isExpanded && hasChildren && (
        <div>
          {folder.children!.map((child) => (
            <FolderTreeItem
              key={child.id}
              folder={child}
              depth={depth + 1}
              selectedFolderId={selectedFolderId}
              onSelect={onSelect}
              onRename={onRename}
              onDelete={onDelete}
              onCreate={onCreate}
            />
          ))}
        </div>
      )}

      {createChild.isCreating && (
        <div style={{ paddingLeft: `${paddingLeft + 16}px` }} className="flex items-center gap-1.5 px-3 py-1.5">
          <FolderIcon className="h-4 w-4 shrink-0 text-yellow-500" />
          <input
            ref={createChild.inputRef}
            type="text"
            value={createChild.name}
            onChange={(e) => createChild.setName(e.target.value)}
            onBlur={handleCreateChild}
            onKeyDown={createChild.onKeyDown}
            placeholder="Folder name"
            className="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5 text-sm text-white outline-none focus:border-yellow-500 placeholder:text-zinc-500"
          />
        </div>
      )}
    </div>
  )
}
