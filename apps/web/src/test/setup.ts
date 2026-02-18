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

// Mock auth API
vi.mock('@/lib/auth-api', () => ({
  getMe: vi.fn(async () => null),
  logout: vi.fn(async () => undefined),
  loginPasskey: vi.fn(async () => ({ user_id: 'test', display_name: 'Test' })),
  registerPasskey: vi.fn(async () => ({ user_id: 'test', display_name: 'Test' })),
  isPasskeySupported: vi.fn(() => true),
}))

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
