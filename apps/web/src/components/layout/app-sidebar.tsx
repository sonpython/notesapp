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
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { useFolders } from '@/hooks/use-folders'
import { FolderTree } from '@/components/folders/folder-tree'

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

  const selectedFolderId = searchParams.get('folder')

  // Fetch folders on mount
  useEffect(() => {
    fetchFolders()
  }, [fetchFolders])

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
        />
      </div>

      {/* User section at bottom */}
      <div className="border-t border-zinc-800 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-xs text-zinc-500">
            {user?.email ?? 'Loading...'}
          </span>
          <button
            type="button"
            onClick={handleSignOut}
            className="shrink-0 rounded p-1.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
            title="Sign out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </aside>
  )
}
