import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from './api'

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should export api with required methods', () => {
    expect(api).toBeDefined()
    expect(api.get).toBeDefined()
    expect(api.post).toBeDefined()
    expect(api.put).toBeDefined()
    expect(api.delete).toBeDefined()
  })

  it('should have working methods as functions', () => {
    expect(typeof api.get).toBe('function')
    expect(typeof api.post).toBe('function')
    expect(typeof api.put).toBe('function')
    expect(typeof api.delete).toBe('function')
  })
})
