import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Cleanup after each test
afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Supabase browser client
vi.mock('@/lib/supabase-browser', () => {
  const mockSupabase = {
    auth: {
      getSession: vi.fn(async () => ({
        data: { session: { access_token: 'mock-token' } },
      })),
      getUser: vi.fn(async () => ({
        data: { user: null },
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
  return {
    createClient: () => mockSupabase,
  }
})

// Mock API client
vi.mock('@/lib/api', () => {
  return {
    api: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  }
})

// Mock fetch globally for API tests
global.fetch = vi.fn()

// Mock console methods to avoid noise in test output
global.console = {
  ...console,
  error: vi.fn(),
  warn: vi.fn(),
  log: vi.fn(),
}
