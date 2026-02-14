'use client'

import { Check } from 'lucide-react'

export const TAG_COLORS = [
  { name: 'Gray', hex: '#6b7280' },
  { name: 'Red', hex: '#ef4444' },
  { name: 'Orange', hex: '#f97316' },
  { name: 'Amber', hex: '#f59e0b' },
  { name: 'Green', hex: '#22c55e' },
  { name: 'Teal', hex: '#14b8a6' },
  { name: 'Blue', hex: '#3b82f6' },
  { name: 'Indigo', hex: '#6366f1' },
  { name: 'Purple', hex: '#a855f7' },
  { name: 'Pink', hex: '#ec4899' },
  { name: 'Rose', hex: '#f43f5e' },
  { name: 'Cyan', hex: '#06b6d4' },
]

interface TagColorPickerProps {
  selected: string
  onChange: (hex: string) => void
}

export function TagColorPicker({ selected, onChange }: TagColorPickerProps) {
  return (
    <div className="grid grid-cols-6 gap-2">
      {TAG_COLORS.map((color) => (
        <button
          key={color.hex}
          type="button"
          onClick={() => onChange(color.hex)}
          className="w-8 h-8 rounded-full flex items-center justify-center hover:scale-110 transition-transform"
          style={{ backgroundColor: color.hex }}
          aria-label={color.name}
          title={color.name}
        >
          {selected === color.hex && (
            <Check className="w-4 h-4 text-white drop-shadow-md" />
          )}
        </button>
      ))}
    </div>
  )
}
