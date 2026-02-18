'use client'

import { useEffect, useState, useCallback } from 'react'
import { getMe, logout as logoutApi, type AuthUser } from '@/lib/auth-api'

/**
 * Custom hook providing auth state: current user, loading status, and sign-out.
 * Uses HttpOnly session cookie - no client-side token handling.
 */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const signOut = useCallback(async () => {
    try {
      await logoutApi()
    } catch {
      // Ignore logout errors - clear local state anyway
    }
    setUser(null)
  }, [])

  return { user, loading, signOut }
}
