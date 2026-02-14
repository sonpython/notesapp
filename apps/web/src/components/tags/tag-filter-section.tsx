'use client'

import { X } from 'lucide-react'
import type { Tag } from '@/lib/types'

interface TagFilterSectionProps {
  tags: Tag[]
  selectedTagIds: string[]
  onToggleTag: (tagId: string) => void
  onClearAll: () => void
}

export function TagFilterSection({ tags, selectedTagIds, onToggleTag, onClearAll }: TagFilterSectionProps) {
  if (tags.length === 0) {
    return (
      <div className="text-xs text-zinc-500 italic px-2">
        No tags yet
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Tags list */}
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => {
          const isSelected = selectedTagIds.includes(tag.id)
          return (
            <button
              key={tag.id}
              onClick={() => onToggleTag(tag.id)}
              className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-all ${
                isSelected
                  ? 'ring-1 ring-offset-1 ring-offset-zinc-900'
                  : 'opacity-70 hover:opacity-100'
              }`}
              style={{
                backgroundColor: `${tag.color}20`,
                color: tag.color,
                ...(isSelected && { ringColor: tag.color }),
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: tag.color }}
              />
              <span>{tag.name}</span>
            </button>
          )
        })}
      </div>

      {/* Clear filters button */}
      {selectedTagIds.length > 0 && (
        <button
          onClick={onClearAll}
          className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-400 transition-colors px-2"
        >
          <X className="w-3 h-3" />
          Clear filters
        </button>
      )}
    </div>
  )
}
