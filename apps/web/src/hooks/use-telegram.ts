'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { TelegramStatus } from '@/lib/types'

interface LinkResponse {
  link_code: string
  bot_username: string
}

/**
 * Custom hook for managing Telegram integration state.
 * Provides fetch, link, and unlink operations against the backend API.
 */
export function useTelegram() {
  const [status, setStatus] = useState<TelegramStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [linkCode, setLinkCode] = useState<string | null>(null)
  const [botUsername, setBotUsername] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  /** Fetch current Telegram connection status */
  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<TelegramStatus>('/api/telegram/status')
      setStatus(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch status'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  /** Request a new link code for connecting Telegram */
  const linkTelegram = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.post<LinkResponse>('/api/telegram/link')
      setLinkCode(data.link_code)
      setBotUsername(data.bot_username)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate link code'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  /** Disconnect Telegram from the account */
  const unlinkTelegram = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      await api.post('/api/telegram/unlink')
      setStatus({ is_linked: false, is_enabled: false, chat_id: null, bot_linked_at: null })
      setLinkCode(null)
      setBotUsername(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to unlink Telegram'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    status,
    loading,
    linkCode,
    botUsername,
    error,
    fetchStatus,
    linkTelegram,
    unlinkTelegram,
  }
}
