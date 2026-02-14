'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Settings,
  MessageCircle,
  Link,
  Unlink,
  Copy,
  Check,
  User,
  LogOut,
} from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import { useTelegram } from '@/hooks/use-telegram'

/**
 * Settings page with Profile and Telegram Integration sections.
 */
export default function SettingsPage() {
  const router = useRouter()
  const { user, loading: authLoading, signOut } = useAuth()
  const {
    status, loading: tgLoading, linkCode, botUsername, error,
    fetchStatus, linkTelegram, unlinkTelegram,
  } = useTelegram()
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

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

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6 md:p-10">
      <div className="mx-auto max-w-2xl space-y-8">
        {/* Page header */}
        <div className="flex items-center gap-3">
          <Settings className="h-6 w-6 text-muted" />
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        </div>

        {/* Profile section */}
        <section className="rounded-xl border border-border bg-sidebar p-6">
          <div className="mb-4 flex items-center gap-2">
            <User className="h-5 w-5 text-muted" />
            <h2 className="text-lg font-semibold text-foreground">Profile</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-muted">
                Email
              </label>
              <p className="mt-1 text-sm text-foreground">
                {authLoading ? 'Loading...' : user?.email ?? 'Unknown'}
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
              <button
                type="button"
                disabled
                className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted opacity-50 cursor-not-allowed"
              >
                Change Password
              </button>
            </div>
          </div>
        </section>

        {/* Telegram integration section */}
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
      </div>
    </div>
  )
}
