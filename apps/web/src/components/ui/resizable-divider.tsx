'use client'

import { useEffect, useRef, useState } from 'react'

interface ResizableDividerProps {
  /** Orientation of the divider */
  orientation?: 'horizontal' | 'vertical'
  /** Called when resize completes with new size in pixels */
  onResize?: (size: number) => void
  /** Optional className for styling */
  className?: string
}

/**
 * Draggable divider for resizing panels.
 * Uses mouse events to track drag and update panel sizes.
 */
export function ResizableDivider({
  orientation = 'vertical',
  onResize,
  className = '',
}: ResizableDividerProps) {
  const [isDragging, setIsDragging] = useState(false)
  const dividerRef = useRef<HTMLDivElement>(null)
  const startPosRef = useRef(0)
  const startSizeRef = useRef(0)

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!dividerRef.current) return

      const delta = orientation === 'vertical'
        ? e.clientX - startPosRef.current
        : e.clientY - startPosRef.current

      const newSize = startSizeRef.current + delta
      onResize?.(newSize)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, orientation, onResize])

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)

    if (orientation === 'vertical') {
      startPosRef.current = e.clientX
      const prevElement = dividerRef.current?.previousElementSibling as HTMLElement
      startSizeRef.current = prevElement?.offsetWidth ?? 0
    } else {
      startPosRef.current = e.clientY
      const prevElement = dividerRef.current?.previousElementSibling as HTMLElement
      startSizeRef.current = prevElement?.offsetHeight ?? 0
    }
  }

  const cursorClass = orientation === 'vertical' ? 'cursor-col-resize' : 'cursor-row-resize'
  const sizeClass = orientation === 'vertical' ? 'w-1' : 'h-1'
  const hoverClass = orientation === 'vertical'
    ? 'hover:w-1.5 active:w-1.5'
    : 'hover:h-1.5 active:h-1.5'

  return (
    <div
      ref={dividerRef}
      onMouseDown={handleMouseDown}
      className={`
        ${sizeClass}
        ${cursorClass}
        ${hoverClass}
        shrink-0
        bg-border
        hover:bg-accent/50
        active:bg-accent
        transition-all
        ${isDragging ? 'bg-accent' : ''}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
    />
  )
}
