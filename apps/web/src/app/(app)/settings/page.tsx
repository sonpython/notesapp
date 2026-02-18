'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import {
  Settings,
  MessageCircle,
  Link,
  Unlink,
  Copy,
  Check,
  User,
  LogOut,
  Tag,
  Download,
  Share,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { useTelegram } from '@/hooks/use-telegram'
import { useTags } from '@/hooks/use-tags'
import { useInstallPrompt } from '@/hooks/use-install-prompt'
import { TagManagementList } from '@/components/tags/tag-management-list'

/**
 * Settings page with Profile and Telegram Integration sections.
 */
export default function SettingsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, loading: authLoading, signOut } = useAuth()
  const {
    status, loading: tgLoading, linkCode, botUsername, error,
    fetchStatus, linkTelegram, unlinkTelegram,
  } = useTelegram()
  const { tags, fetchTags, createTag, updateTag, deleteTag } = useTags()
  const { canInstall, isInstalled, isIOS, install } = useInstallPrompt()
  const [copied, setCopied] = useState(false)

  const activeTab = searchParams.get('tab') || 'profile'

  useEffect(() => {
    fetchStatus()
    fetchTags()
  }, [fetchStatus, fetchTags])

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const handleCopyCode = async () => {
    if (!linkCode) return
    try {
      await navigator.clipboard.writeText(`/start ${linkCode}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API may fail in some contexts
    }
  }

  const handleCreateTag = async (name: string, color: string) => {
    const tag = await createTag({ name, color })
    if (tag) await fetchTags()
    return tag
  }

  const handleUpdateTag = async (id: string, name: string, color: string) => {
    const tag = await updateTag(id, { name, color })
    if (tag) await fetchTags()
    return tag
  }

  const handleDeleteTag = async (id: string) => {
    const success = await deleteTag(id)
    if (success) await fetchTags()
    return success
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6 md:p-10">
      <div className="mx-auto max-w-2xl space-y-8">
        {/* Page header */}
        <div className="flex items-center gap-3">
          <Settings className="h-6 w-6 text-muted" />
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        </div>

        {/* Tab navigation */}
        <nav className="flex gap-4 border-b border-border">
          <button
            onClick={() => router.push('/settings')}
            className={`pb-2 px-1 text-sm font-medium transition-colors ${
              activeTab === 'profile'
                ? 'border-b-2 border-accent text-accent'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => router.push('/settings?tab=tags')}
            className={`pb-2 px-1 text-sm font-medium transition-colors ${
              activeTab === 'tags'
                ? 'border-b-2 border-accent text-accent'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Tags
          </button>
          <button
            onClick={() => router.push('/settings?tab=telegram')}
            className={`pb-2 px-1 text-sm font-medium transition-colors ${
              activeTab === 'telegram'
                ? 'border-b-2 border-accent text-accent'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Telegram
          </button>
          <button
            onClick={() => router.push('/settings?tab=pwa')}
            className={`pb-2 px-1 text-sm font-medium transition-colors ${
              activeTab === 'pwa'
                ? 'border-b-2 border-accent text-accent'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Install App
          </button>
        </nav>

        {/* Profile section */}
        {activeTab === 'profile' && (
        <section className="rounded-xl border border-border bg-sidebar p-6">
          <div className="mb-4 flex items-center gap-2">
            <User className="h-5 w-5 text-muted" />
            <h2 className="text-lg font-semibold text-foreground">Profile</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-muted">
                Display Name
              </label>
              <p className="mt-1 text-sm text-foreground">
                {authLoading ? 'Loading...' : user?.display_name ?? 'Unknown'}
              </p>
            </div>

            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-muted">
                Authentication
              </label>
              <p className="mt-1 text-sm text-muted">
                Secured with passkey (Face ID, Touch ID, or device PIN)
              </p>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="button"
                onClick={handleSignOut}
                className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-zinc-800"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          </div>
        </section>
        )}

        {/* Tags section */}
        {activeTab === 'tags' && (
        <section className="rounded-xl border border-border bg-sidebar p-6">
          <div className="mb-4 flex items-center gap-2">
            <Tag className="h-5 w-5 text-muted" />
            <h2 className="text-lg font-semibold text-foreground">Tags</h2>
          </div>
          <TagManagementList
            tags={tags}
            onCreate={handleCreateTag}
            onUpdate={handleUpdateTag}
            onDelete={handleDeleteTag}
          />
        </section>
        )}

        {/* PWA Install section */}
        {activeTab === 'pwa' && (
        <section className="rounded-xl border border-border bg-sidebar p-6">
          <div className="mb-4 flex items-center gap-2">
            <Download className="h-5 w-5 text-muted" />
            <h2 className="text-lg font-semibold text-foreground">
              Install NotesApp
            </h2>
          </div>

          {isInstalled ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-green-400">
                <Check className="h-4 w-4" />
                <span>App is installed</span>
              </div>
              <p className="text-sm text-muted">
                NotesApp is installed and can be used offline. You can access it
                from your home screen or app launcher.
              </p>
            </div>
          ) : canInstall ? (
            <div className="space-y-4">
              <p className="text-sm text-muted">
                Install NotesApp for a better experience with offline access,
                faster performance, and easier access from your home screen.
              </p>
              <button
                type="button"
                onClick={install}
                className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90"
              >
                <Download className="h-4 w-4" />
                Install App
              </button>
            </div>
          ) : isIOS ? (
            <div className="space-y-4">
              <p className="text-sm text-muted">
                To install NotesApp on your iPhone or iPad:
              </p>
              <ol className="list-decimal space-y-2 pl-5 text-sm text-muted">
                <li>Tap the Share button <Share className="inline h-3.5 w-3.5" /> in Safari</li>
                <li>Scroll down and tap &ldquo;Add to Home Screen&rdquo;</li>
                <li>Tap &ldquo;Add&rdquo; to confirm</li>
              </ol>
              <p className="text-sm text-muted">
                Once installed, you can use NotesApp offline and access it from
                your home screen.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted">
                NotesApp can be installed as a standalone app for offline access
                and better performance. Install option will appear when using a
                compatible browser (Chrome, Edge, Safari on iOS).
              </p>
            </div>
          )}
        </section>
        )}

        {/* Telegram integration section */}
        {activeTab === 'telegram' && (
        <section className="rounded-xl border border-border bg-sidebar p-6">
          <div className="mb-4 flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-muted" />
            <h2 className="text-lg font-semibold text-foreground">
              Telegram Integration
            </h2>
          </div>

          {error && (
            <p className="mb-4 rounded-lg bg-red-900/30 px-4 py-2 text-sm text-red-400">
              {error}
            </p>
          )}

          {/* Connected state */}
          {status?.is_linked && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-green-400">
                <Link className="h-4 w-4" />
                <span>Connected</span>
              </div>
              {status.bot_linked_at && (
                <p className="text-xs text-muted">
                  Linked on{' '}
                  {new Date(status.bot_linked_at).toLocaleDateString(undefined, {
                    year: 'numeric', month: 'long', day: 'numeric',
                  })}
                </p>
              )}
              <button
                type="button"
                onClick={unlinkTelegram}
                disabled={tgLoading}
                className="inline-flex items-center gap-2 rounded-lg border border-red-800 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-900/30 disabled:opacity-50"
              >
                <Unlink className="h-4 w-4" />
                {tgLoading ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          )}

          {/* Not connected, no link code yet */}
          {!status?.is_linked && !linkCode && (
            <div className="space-y-3">
              <p className="text-sm text-muted">
                Connect Telegram to receive note reminders and manage todos from
                your phone.
              </p>
              <button
                type="button"
                onClick={linkTelegram}
                disabled={tgLoading}
                className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                <Link className="h-4 w-4" />
                {tgLoading ? 'Generating...' : 'Connect Telegram'}
              </button>
            </div>
          )}

          {/* Link code displayed */}
          {!status?.is_linked && linkCode && botUsername && (
            <div className="space-y-4">
              <p className="text-sm text-muted">
                Send the following command to{' '}
                <span className="font-semibold text-foreground">
                  @{botUsername}
                </span>{' '}
                on Telegram:
              </p>
              <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-3">
                <code className="flex-1 font-mono text-sm text-accent">
                  /start {linkCode}
                </code>
                <button
                  type="button"
                  onClick={handleCopyCode}
                  className="shrink-0 rounded-md p-1.5 text-muted transition-colors hover:bg-zinc-800 hover:text-foreground"
                  title="Copy command"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-400" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-muted">
                After sending the command, refresh this page to confirm the
                connection.
              </p>
            </div>
          )}
        </section>
        )}
      </div>
    </div>
  )
}
