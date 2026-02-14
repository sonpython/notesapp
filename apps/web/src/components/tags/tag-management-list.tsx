'use client'

import { useState } from 'react'
import { Plus, Edit2, Trash2, Check, X } from 'lucide-react'
import { TagColorPicker, TAG_COLORS } from './tag-color-picker'
import type { Tag } from '@/lib/types'

interface TagManagementListProps {
  tags: Tag[]
  onCreate: (name: string, color: string) => Promise<Tag | null>
  onUpdate: (id: string, name: string, color: string) => Promise<Tag | null>
  onDelete: (id: string) => Promise<boolean>
}

export function TagManagementList({ tags, onCreate, onUpdate, onDelete }: TagManagementListProps) {
  const [isCreating, setIsCreating] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [newTagColor, setNewTagColor] = useState(TAG_COLORS[0].hex)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editColor, setEditColor] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!newTagName.trim()) return
    const created = await onCreate(newTagName.trim(), newTagColor)
    if (created) {
      setNewTagName('')
      setNewTagColor(TAG_COLORS[0].hex)
      setIsCreating(false)
    }
  }

  const handleUpdate = async (id: string) => {
    if (!editName.trim()) return
    const updated = await onUpdate(id, editName.trim(), editColor)
    if (updated) {
      setEditingId(null)
    }
  }

  const handleDelete = async (id: string) => {
    const success = await onDelete(id)
    if (success) {
      setDeleteConfirmId(null)
    }
  }

  const startEdit = (tag: Tag) => {
    setEditingId(tag.id)
    setEditName(tag.name)
    setEditColor(tag.color)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditName('')
    setEditColor('')
  }

  return (
    <div className="space-y-4">
      {/* Header with create button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-zinc-200">Tags</h3>
        {!isCreating && (
          <button
            onClick={() => setIsCreating(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Tag
          </button>
        )}
      </div>

      {/* Create new tag form */}
      {isCreating && (
        <div className="p-4 bg-zinc-800 border border-zinc-700 rounded-lg space-y-3">
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-1.5">
              Tag name
            </label>
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="Enter tag name"
              className="w-full px-3 py-2 bg-zinc-900 text-zinc-200 placeholder-zinc-500 border border-zinc-700 rounded outline-none focus:border-amber-500"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreate()
                if (e.key === 'Escape') {
                  setIsCreating(false)
                  setNewTagName('')
                  setNewTagColor(TAG_COLORS[0].hex)
                }
              }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-2">
              Color
            </label>
            <TagColorPicker selected={newTagColor} onChange={setNewTagColor} />
          </div>
          <div className="flex gap-2 pt-2">
            <button
              onClick={handleCreate}
              className="flex-1 px-4 py-2 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
            >
              Create Tag
            </button>
            <button
              onClick={() => {
                setIsCreating(false)
                setNewTagName('')
                setNewTagColor(TAG_COLORS[0].hex)
              }}
              className="flex-1 px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Tags list */}
      {tags.length === 0 ? (
        <div className="text-center py-8 text-zinc-500 text-sm">
          No tags created yet. Add your first tag to get started.
        </div>
      ) : (
        <div className="space-y-2">
          {tags.map((tag) => (
            <div
              key={tag.id}
              className="p-3 bg-zinc-800 border border-zinc-700 rounded-lg"
            >
              {editingId === tag.id ? (
                // Edit mode
                <div className="space-y-3">
                  <div>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full px-3 py-2 bg-zinc-900 text-zinc-200 border border-zinc-700 rounded outline-none focus:border-amber-500"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleUpdate(tag.id)
                        if (e.key === 'Escape') cancelEdit()
                      }}
                    />
                  </div>
                  <TagColorPicker selected={editColor} onChange={setEditColor} />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleUpdate(tag.id)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
                    >
                      <Check className="w-4 h-4" />
                      Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                    >
                      <X className="w-4 h-4" />
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: tag.color }}
                    />
                    <span className="text-sm font-medium text-zinc-200">{tag.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => startEdit(tag)}
                      className="p-1.5 text-zinc-400 hover:text-zinc-300 hover:bg-zinc-700 rounded transition-colors"
                      title="Edit tag"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    {deleteConfirmId === tag.id ? (
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-zinc-400 mr-1">Delete?</span>
                        <button
                          onClick={() => handleDelete(tag.id)}
                          className="px-2 py-1 text-xs font-medium text-red-400 hover:text-red-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                        >
                          Yes
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(null)}
                          className="px-2 py-1 text-xs font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                        >
                          No
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirmId(tag.id)}
                        className="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-zinc-700 rounded transition-colors"
                        title="Delete tag"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
