'use client'

import { X } from 'lucide-react'

interface TagPillProps {
  name: string
  color: string
  onRemove?: () => void
  size?: 'sm' | 'md'
}

export function TagPill({ name, color, onRemove, size = 'sm' }: TagPillProps) {
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeClasses} font-medium`}
      style={{
        backgroundColor: `${color}20`,
        color: color,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span>{name}</span>
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="hover:opacity-70 transition-opacity"
          aria-label={`Remove ${name} tag`}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </span>
  )
}
