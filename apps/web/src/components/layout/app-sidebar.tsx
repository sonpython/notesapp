'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  FileText,
  CheckSquare,
  Settings,
  LogOut,
  Plus,
  FolderIcon,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'

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
  const { user, signOut } = useAuth()

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
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

      {/* Folder list placeholder - scrollable area */}
      <div className="flex-1 overflow-y-auto px-3">
        <FolderTreePlaceholder />
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

/**
 * Placeholder for the folder tree. Displays an empty-state hint
 * when no folders exist yet.
 */
function FolderTreePlaceholder() {
  return (
    <div className="flex flex-col items-center gap-2 py-6 text-center">
      <FolderIcon className="h-8 w-8 text-zinc-700" />
      <p className="text-xs text-zinc-600">No folders yet</p>
      <button
        type="button"
        className="flex items-center gap-1.5 rounded-md bg-zinc-800 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-zinc-300"
      >
        <Plus className="h-3 w-3" />
        New Folder
      </button>
    </div>
  )
}
