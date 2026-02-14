// FastAPI client wrapper that automatically includes Supabase auth token
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

import { createClient } from './supabase-browser'

class ApiClient {
  private supabase = createClient()

  private async getHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = { 'Content-Type': 'application/json' }
    try {
      const { data: { session } } = await this.supabase.auth.getSession()
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      } else {
        console.warn('[api] No session/access_token available')
      }
    } catch (err) {
      console.error('[api] Failed to get session:', err)
    }
    return headers
  }

  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_URL}${path}`, { headers: await this.getHeaders() })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    return res.json()
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    return res.json()
  }

  async put<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'PUT',
      headers: await this.getHeaders(),
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    return res.json()
  }

  async delete(path: string): Promise<void> {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'DELETE',
      headers: await this.getHeaders(),
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
  }
}

export const api = new ApiClient()
