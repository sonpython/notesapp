'use client'

import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect } from 'react'
import {
  FileText,
  CheckSquare,
  Settings,
  LogOut,
  Plus,
  Tag as TagIcon,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { useFolders } from '@/hooks/use-folders'
import { useNotes } from '@/hooks/use-notes'
import { useTags } from '@/hooks/use-tags'
import { FolderTree } from '@/components/folders/folder-tree'
import { ThemeToggleButton } from '@/components/ui/theme-toggle-button'
import { TagFilterSection } from '@/components/tags/tag-filter-section'

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const navItems: NavItem[] = [
  { label: 'Notes', href: '/notes', icon: FileText },
  { label: 'Todos', href: '/todos', icon: CheckSquare },
  { label: 'Settings', href: '/settings', icon: Settings },
]

/**
 * App sidebar with navigation, folder tree, and user controls.
 * Apple Notes-inspired dark sidebar (zinc-900).
 */
export function AppSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, signOut } = useAuth()
  const {
    folderTree,
    fetchFolders,
    createFolder,
    updateFolder,
    deleteFolder,
  } = useFolders()
  const { moveNoteToFolder } = useNotes()
  const { tags, fetchTags } = useTags()

  const selectedFolderId = searchParams.get('folder')
  const tagIdsParam = searchParams.get('tags')
  const selectedTagIds = tagIdsParam ? tagIdsParam.split(',') : []

  // Fetch folders and tags on mount
  useEffect(() => {
    fetchFolders()
    fetchTags()
  }, [fetchFolders, fetchTags])

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const handleSelectFolder = (id: string | null) => {
    if (id) {
      router.push(`/notes?folder=${id}`)
    } else {
      router.push('/notes')
    }
  }

  const handleCreateFolder = async (name: string, parentId?: string) => {
    return createFolder(name, parentId)
  }

  const handleRenameFolder = async (id: string, name: string) => {
    return updateFolder(id, { name })
  }

  const handleDeleteFolder = async (id: string) => {
    await deleteFolder(id)
    // If deleted folder was selected, navigate to all notes
    if (selectedFolderId === id) {
      router.push('/notes')
    }
  }

  const handleNewFolderClick = () => {
    // Trigger root folder creation by setting a flag
    // For simplicity, we'll let FolderTree handle its own creation state
    // The Plus button in header could trigger tree's internal state
    // For now, user can click "New Folder" button in empty state or context menu
  }

  const handleToggleTag = (tagId: string) => {
    const newTagIds = selectedTagIds.includes(tagId)
      ? selectedTagIds.filter(id => id !== tagId)
      : [...selectedTagIds, tagId]

    const params = new URLSearchParams(searchParams.toString())
    if (newTagIds.length > 0) {
      params.set('tags', newTagIds.join(','))
    } else {
      params.delete('tags')
    }
    router.push(`${pathname}?${params.toString()}`)
  }

  const handleClearTagFilters = () => {
    const params = new URLSearchParams(searchParams.toString())
    params.delete('tags')
    router.push(`${pathname}?${params.toString()}`)
  }

  return (
    <aside className="flex h-full w-64 flex-col bg-zinc-900 text-zinc-300">
      {/* App title */}
      <div className="flex h-14 items-center px-5">
        <h1 className="text-lg font-semibold tracking-tight text-white">
          NotesApp
        </h1>
      </div>

      {/* Navigation links */}
      <nav className="space-y-0.5 px-3">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-zinc-700/60 text-white'
                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* Divider */}
      <div className="mx-5 my-3 border-t border-zinc-800" />

      {/* Folder tree section */}
      <div className="flex items-center justify-between px-5 pb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Folders
        </span>
        <button
          type="button"
          className="rounded p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
          title="New Folder"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Folder list - scrollable area */}
      <div className="flex-1 overflow-y-auto px-3">
        <FolderTree
          folders={folderTree}
          selectedFolderId={selectedFolderId}
          onSelectFolder={handleSelectFolder}
          onCreateFolder={handleCreateFolder}
          onRenameFolder={handleRenameFolder}
          onDeleteFolder={handleDeleteFolder}
          onMoveNote={moveNoteToFolder}
        />
      </div>

      {/* Divider */}
      <div className="mx-5 my-3 border-t border-zinc-800" />

      {/* Tags section */}
      <div className="flex items-center justify-between px-5 pb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Tags
        </span>
        <Link
          href="/settings?tab=tags"
          className="rounded p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
          title="Manage Tags"
        >
          <TagIcon className="h-3.5 w-3.5" />
        </Link>
      </div>
      <div className="px-3 pb-3">
        <TagFilterSection
          tags={tags}
          selectedTagIds={selectedTagIds}
          onToggleTag={handleToggleTag}
          onClearAll={handleClearTagFilters}
        />
      </div>

      {/* User section at bottom */}
      <div className="border-t border-zinc-800 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-xs text-zinc-500">
            {user?.email ?? 'Loading...'}
          </span>
          <div className="flex shrink-0 items-center gap-1">
            <ThemeToggleButton />
            <button
              type="button"
              onClick={handleSignOut}
              className="rounded p-1.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}
