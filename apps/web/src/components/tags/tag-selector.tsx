'use client'

import { useState, useRef, useEffect } from 'react'
import { Plus, Search } from 'lucide-react'
import { TagPill } from './tag-pill'
import { TagColorPicker, TAG_COLORS } from './tag-color-picker'
import type { Tag } from '@/lib/types'

interface TagSelectorProps {
  selectedTags: Tag[]
  allTags: Tag[]
  onAdd: (tagId: string) => void
  onRemove: (tagId: string) => void
  onCreate: (name: string, color: string) => Promise<Tag | null>
}

export function TagSelector({ selectedTags, allTags, onAdd, onRemove, onCreate }: TagSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [newTagColor, setNewTagColor] = useState(TAG_COLORS[0].hex)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setIsCreating(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const availableTags = allTags.filter(
    (tag) => !selectedTags.some((st) => st.id === tag.id)
  )

  const filteredTags = availableTags.filter((tag) =>
    tag.name.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return
    const created = await onCreate(newTagName.trim(), newTagColor)
    if (created) {
      onAdd(created.id)
      setNewTagName('')
      setNewTagColor(TAG_COLORS[0].hex)
      setIsCreating(false)
      setSearch('')
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selected tags display */}
      <div className="flex flex-wrap items-center gap-2">
        {selectedTags.map((tag) => (
          <TagPill
            key={tag.id}
            name={tag.name}
            color={tag.color}
            onRemove={() => onRemove(tag.id)}
          />
        ))}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-800 hover:bg-zinc-700 rounded-full transition-colors"
        >
          <Plus className="w-3 h-3" />
          Add tag
        </button>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-2 w-64 bg-zinc-800 border border-zinc-700 rounded-lg shadow-lg z-50">
          {/* Search input */}
          {!isCreating && (
            <div className="p-2 border-b border-zinc-700">
              <div className="flex items-center gap-2 px-2 py-1.5 bg-zinc-900 rounded">
                <Search className="w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search tags..."
                  className="flex-1 bg-transparent text-sm text-zinc-200 placeholder-zinc-500 outline-none"
                  autoFocus
                />
              </div>
            </div>
          )}

          {/* Tag list or create form */}
          <div className="max-h-48 overflow-y-auto">
            {isCreating ? (
              <div className="p-3 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">
                    Tag name
                  </label>
                  <input
                    type="text"
                    value={newTagName}
                    onChange={(e) => setNewTagName(e.target.value)}
                    placeholder="Enter tag name"
                    className="w-full px-2 py-1.5 bg-zinc-900 text-sm text-zinc-200 placeholder-zinc-500 border border-zinc-700 rounded outline-none focus:border-amber-500"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreateTag()
                      if (e.key === 'Escape') setIsCreating(false)
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-2">
                    Color
                  </label>
                  <TagColorPicker selected={newTagColor} onChange={setNewTagColor} />
                </div>
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={handleCreateTag}
                    className="flex-1 px-3 py-1.5 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
                  >
                    Create
                  </button>
                  <button
                    onClick={() => {
                      setIsCreating(false)
                      setNewTagName('')
                      setNewTagColor(TAG_COLORS[0].hex)
                    }}
                    className="flex-1 px-3 py-1.5 text-sm font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                {filteredTags.length === 0 && search && (
                  <div className="p-3 text-center">
                    <p className="text-sm text-zinc-500 mb-2">No tags found</p>
                    <button
                      onClick={() => {
                        setNewTagName(search)
                        setIsCreating(true)
                      }}
                      className="text-sm text-amber-500 hover:text-amber-400"
                    >
                      Create &quot;{search}&quot;
                    </button>
                  </div>
                )}
                {filteredTags.map((tag) => (
                  <button
                    key={tag.id}
                    onClick={() => {
                      onAdd(tag.id)
                      setSearch('')
                    }}
                    className="w-full px-3 py-2 flex items-center gap-2 hover:bg-zinc-700 transition-colors text-left"
                  >
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tag.color }}
                    />
                    <span className="text-sm text-zinc-200">{tag.name}</span>
                  </button>
                ))}
                {!isCreating && filteredTags.length > 0 && (
                  <div className="border-t border-zinc-700">
                    <button
                      onClick={() => setIsCreating(true)}
                      className="w-full px-3 py-2 flex items-center gap-2 text-amber-500 hover:bg-zinc-700 transition-colors text-sm"
                    >
                      <Plus className="w-4 h-4" />
                      Create new tag
                    </button>
                  </div>
                )}
                {!isCreating && filteredTags.length === 0 && !search && (
                  <button
                    onClick={() => setIsCreating(true)}
                    className="w-full px-3 py-2 flex items-center gap-2 text-amber-500 hover:bg-zinc-700 transition-colors text-sm"
                  >
                    <Plus className="w-4 h-4" />
                    Create new tag
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
