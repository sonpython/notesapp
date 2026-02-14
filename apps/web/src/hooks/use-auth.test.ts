import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAuth } from './use-auth'
import * as supabaseModule from '@/lib/supabase-browser'

describe('useAuth', () => {
  const mockUser = {
    id: 'user123',
    email: 'test@example.com',
    user_metadata: {},
    app_metadata: {},
    aud: 'authenticated',
    created_at: '2026-02-15T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useAuth())

    expect(result.current.loading).toBe(true)
    expect(result.current.user).toBeNull()
  })

  it('should fetch initial user on mount', async () => {
    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: mockUser },
          error: null,
        })),
        onAuthStateChange: vi.fn(() => ({
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        })),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toEqual(mockUser)
    expect(mockSupabase.auth.getUser).toHaveBeenCalled()
  })

  it('should handle initial user fetch error', async () => {
    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: null },
          error: new Error('Failed to fetch user'),
        })),
        onAuthStateChange: vi.fn(() => ({
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        })),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toBeNull()
  })

  it('should listen to auth state changes', async () => {
    const mockUnsubscribe = vi.fn()
    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: null },
          error: null,
        })),
        onAuthStateChange: vi.fn((callback) => {
          // Simulate auth state change
          setTimeout(() => {
            callback('SIGNED_IN', { user: mockUser, access_token: 'token' })
          }, 0)

          return {
            data: {
              subscription: {
                unsubscribe: mockUnsubscribe,
              },
            },
          }
        }),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result, unmount } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })

    expect(result.current.loading).toBe(false)

    unmount()

    await waitFor(() => {
      expect(mockUnsubscribe).toHaveBeenCalled()
    })
  })

  it('should handle sign out', async () => {
    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: mockUser },
          error: null,
        })),
        onAuthStateChange: vi.fn(() => ({
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        })),
        signOut: vi.fn(async () => ({ error: null })),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.signOut()
    })

    expect(mockSupabase.auth.signOut).toHaveBeenCalled()
  })

  it('should handle sign out error gracefully', async () => {
    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: mockUser },
          error: null,
        })),
        onAuthStateChange: vi.fn(() => ({
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        })),
        signOut: vi.fn(async () => {
          throw new Error('Sign out failed')
        }),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Should not throw
    await act(async () => {
      await result.current.signOut()
    })

    expect(mockSupabase.auth.signOut).toHaveBeenCalled()
  })

  it('should update user when auth state changes to SIGNED_IN', async () => {
    let authCallback: ((event: string, session: any) => void) | null = null

    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: null },
          error: null,
        })),
        onAuthStateChange: vi.fn((callback) => {
          authCallback = callback
          return {
            data: {
              subscription: {
                unsubscribe: vi.fn(),
              },
            },
          }
        }),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toBeNull()

    // Simulate sign in
    await act(async () => {
      authCallback?.('SIGNED_IN', { user: mockUser })
    })

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })
  })

  it('should clear user when auth state changes to SIGNED_OUT', async () => {
    let authCallback: ((event: string, session: any) => void) | null = null

    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: mockUser },
          error: null,
        })),
        onAuthStateChange: vi.fn((callback) => {
          authCallback = callback
          return {
            data: {
              subscription: {
                unsubscribe: vi.fn(),
              },
            },
          }
        }),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })

    // Simulate sign out
    await act(async () => {
      authCallback?.('SIGNED_OUT', null)
    })

    await waitFor(() => {
      expect(result.current.user).toBeNull()
    })
  })

  it('should unsubscribe from auth changes on unmount', async () => {
    const mockUnsubscribe = vi.fn()
    const mockSupabase = {
      auth: {
        getUser: vi.fn(async () => ({
          data: { user: null },
          error: null,
        })),
        onAuthStateChange: vi.fn(() => ({
          data: {
            subscription: {
              unsubscribe: mockUnsubscribe,
            },
          },
        })),
      },
    }

    vi.spyOn(supabaseModule, 'createClient').mockReturnValue(mockSupabase as any)

    const { unmount } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(mockSupabase.auth.onAuthStateChange).toHaveBeenCalled()
    })

    unmount()

    expect(mockUnsubscribe).toHaveBeenCalled()
  })
})
