import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAuth } from './use-auth'
import * as authApi from '@/lib/auth-api'

describe('useAuth', () => {
  const mockUser = {
    user_id: 'user123',
    display_name: 'Test User',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with loading state', () => {
    vi.spyOn(authApi, 'getMe').mockImplementation(() => new Promise(() => {}))

    const { result } = renderHook(() => useAuth())

    expect(result.current.loading).toBe(true)
    expect(result.current.user).toBeNull()
  })

  it('should fetch initial user on mount', async () => {
    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toEqual(mockUser)
    expect(authApi.getMe).toHaveBeenCalled()
  })

  it('should handle user not authenticated', async () => {
    vi.spyOn(authApi, 'getMe').mockResolvedValue(null)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toBeNull()
  })

  it('should handle fetch error', async () => {
    vi.spyOn(authApi, 'getMe').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toBeNull()
  })

  it('should handle sign out', async () => {
    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser)
    vi.spyOn(authApi, 'logout').mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.user).toEqual(mockUser)

    await act(async () => {
      await result.current.signOut()
    })

    expect(authApi.logout).toHaveBeenCalled()
    expect(result.current.user).toBeNull()
  })

  it('should handle sign out even if logout fails', async () => {
    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser)
    vi.spyOn(authApi, 'logout').mockRejectedValue(new Error('Logout failed'))

    const { result } = renderHook(() => useAuth())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Should not throw, user should still be cleared locally
    await act(async () => {
      await result.current.signOut()
    })

    expect(result.current.user).toBeNull()
  })
})
