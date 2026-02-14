'use client'

import { useRef, useEffect } from 'react'
import { MoreHorizontal, Pencil, FolderPlus, Trash2 } from 'lucide-react'

interface FolderContextMenuProps {
  show: boolean
  onClose: () => void
  onRename: () => void
  onNewSubfolder: () => void
  onDelete: () => void
}

/**
 * Context menu for folder actions (rename, new subfolder, delete).
 * Closes on outside click or menu item selection.
 */
export function FolderContextMenu({
  show,
  onClose,
  onRename,
  onNewSubfolder,
  onDelete,
}: FolderContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!show) return
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [show, onClose])

  if (!show) return null

  return (
    <div
      ref={menuRef}
      className="absolute right-0 top-full mt-1 w-40 rounded-md bg-zinc-800 border border-zinc-700 shadow-lg z-10 py-1"
    >
      <button
        onClick={(e) => { e.stopPropagation(); onRename(); onClose() }}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 text-left"
      >
        <Pencil className="h-3 w-3" />
        Rename
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onNewSubfolder(); onClose() }}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 text-left"
      >
        <FolderPlus className="h-3 w-3" />
        New Subfolder
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete() }}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-zinc-700 text-left"
      >
        <Trash2 className="h-3 w-3" />
        Delete
      </button>
    </div>
  )
}

export function FolderMenuTrigger({
  onClick,
}: {
  onClick: (e: React.MouseEvent) => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="opacity-0 group-hover:opacity-100 shrink-0 p-0.5 rounded hover:bg-zinc-700"
    >
      <MoreHorizontal className="h-3.5 w-3.5" />
    </button>
  )
}
