'use client'

import { Download, FileDown, FileText, FolderArchive } from 'lucide-react'
import { useState } from 'react'
import type { Note } from '@/lib/types'

interface NoteExportMenuProps {
  note: Note | null
  onExportAll?: () => Promise<void>
}

/**
 * Export menu dropdown for single note or bulk export.
 * Provides markdown, PDF, and bulk ZIP export options.
 */
export function NoteExportMenu({ note, onExportAll }: NoteExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const handleExportMarkdown = async () => {
    if (!note) return
    setIsExporting(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/notes/${note.id}/export/md`, {
        credentials: 'include',
      })
      if (!response.ok) throw new Error('Export failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${note.title || 'untitled'}.md`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setIsOpen(false)
    } catch (error) {
      console.error('Markdown export failed:', error)
      alert('Failed to export markdown')
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportPdf = async () => {
    if (!note) return
    setIsExporting(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/notes/${note.id}/export/pdf`, {
        credentials: 'include',
      })
      if (!response.ok) throw new Error('Export failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${note.title || 'untitled'}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setIsOpen(false)
    } catch (error) {
      console.error('PDF export failed:', error)
      alert('Failed to export PDF')
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportAllZip = async () => {
    if (!onExportAll) return
    setIsExporting(true)
    try {
      await onExportAll()
      setIsOpen(false)
    } catch (error) {
      console.error('Bulk export failed:', error)
      alert('Failed to export all notes')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="p-1.5 rounded-md transition-colors cursor-pointer text-muted hover:text-foreground hover:bg-sidebar disabled:opacity-50"
        title="Export"
      >
        <Download className="w-4 h-4" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown menu */}
          <div className="absolute right-0 top-full mt-1 w-48 bg-background border border-border rounded-md shadow-lg z-20 py-1">
            {note && (
              <>
                <button
                  onClick={handleExportMarkdown}
                  disabled={isExporting}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-sidebar flex items-center gap-2 text-foreground disabled:opacity-50"
                >
                  <FileText className="w-4 h-4" />
                  Export as Markdown
                </button>
                <button
                  onClick={handleExportPdf}
                  disabled={isExporting}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-sidebar flex items-center gap-2 text-foreground disabled:opacity-50"
                >
                  <FileDown className="w-4 h-4" />
                  Export as PDF
                </button>
                {onExportAll && <div className="border-t border-border my-1" />}
              </>
            )}
            {onExportAll && (
              <button
                onClick={handleExportAllZip}
                disabled={isExporting}
                className="w-full text-left px-3 py-2 text-sm hover:bg-sidebar flex items-center gap-2 text-foreground disabled:opacity-50"
              >
                <FolderArchive className="w-4 h-4" />
                Export All as ZIP
              </button>
            )}
          </div>
        </>
      )}
    </div>
  )
}
