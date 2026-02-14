import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useNotes } from './use-notes'
import { api } from '@/lib/api'
import type { Note, PaginatedResponse } from '@/lib/types'

vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 })

describe('useNotes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useNotes())

    expect(result.current.notes).toEqual([])
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should fetch notes successfully', async () => {
    const mockNotes: Note[] = [
      {
        id: '1',
        user_id: 'user1',
        title: 'Test Note',
        content: 'Test content',
        folder_id: null,
        is_pinned: false,
        is_archived: false,
        created_at: '2026-02-15T00:00:00Z',
        updated_at: '2026-02-15T00:00:00Z',
        tags: [],
      },
    ]

    const mockResponse: PaginatedResponse<Note> = {
      items: mockNotes,
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useNotes())

    expect(result.current.loading).toBe(false)

    await act(async () => {
      await result.current.fetchNotes()
    })

    expect(result.current.notes).toEqual(mockNotes)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(api.get).toHaveBeenCalledWith('/api/notes?limit=50&offset=0')
  })

  it('should fetch notes with folder filter', async () => {
    const mockResponse: PaginatedResponse<Note> = {
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useNotes())

    await act(async () => {
      await result.current.fetchNotes('folder1')
    })

    expect(api.get).toHaveBeenCalledWith('/api/notes?folder_id=folder1&limit=50&offset=0')
  })

  it('should fetch notes with search query', async () => {
    const mockResponse: PaginatedResponse<Note> = {
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useNotes())

    await act(async () => {
      await result.current.fetchNotes(undefined, 'search term')
    })

    expect(api.get).toHaveBeenCalled()
    const call = vi.mocked(api.get).mock.calls[0][0]
    expect(call).toContain('search=search')
  })

  it('should fetch notes with both folder and search', async () => {
    const mockResponse: PaginatedResponse<Note> = {
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useNotes())

    await act(async () => {
      await result.current.fetchNotes('folder1', 'search')
    })

    expect(api.get).toHaveBeenCalledWith('/api/notes?folder_id=folder1&search=search&limit=50&offset=0')
  })

  it('should handle fetch error', async () => {
    const errorMessage = 'Failed to fetch notes'
    vi.mocked(api.get).mockRejectedValueOnce(new Error(errorMessage))

    const { result } = renderHook(() => useNotes())

    await act(async () => {
      await result.current.fetchNotes()
    })

    expect(result.current.error).toBe(errorMessage)
    expect(result.current.notes).toEqual([])
  })

  it('should create note and add to list', async () => {
    const newNote: Note = {
      id: '2',
      user_id: 'user1',
      title: 'New Note',
      content: 'New content',
      folder_id: null,
      is_pinned: false,
      is_archived: false,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
      tags: [],
    }

    vi.mocked(api.post).mockResolvedValueOnce(newNote)

    const { result } = renderHook(() => useNotes())

    let createdNote: Note | undefined
    await act(async () => {
      createdNote = await result.current.createNote({ title: 'New Note', content: 'New content' })
    })

    expect(createdNote).toEqual(newNote)
    expect(result.current.notes).toContainEqual(newNote)
    expect(api.post).toHaveBeenCalledWith('/api/notes', { title: 'New Note', content: 'New content' })
  })

  it('should throw error on create failure', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Create failed'))

    const { result } = renderHook(() => useNotes())

    let threwError = false
    try {
      await act(async () => {
        await result.current.createNote({ title: 'New Note' })
      })
    } catch (err) {
      threwError = true
    }

    expect(threwError).toBe(true)
  })

  it('should update note in list', async () => {
    const existingNote: Note = {
      id: '1',
      user_id: 'user1',
      title: 'Test Note',
      content: 'Test content',
      folder_id: null,
      is_pinned: false,
      is_archived: false,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
      tags: [],
    }

    const updatedNote: Note = {
      ...existingNote,
      title: 'Updated Note',
    }

    const mockResponse: PaginatedResponse<Note> = {
      items: [existingNote],
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useNotes())

    // First fetch notes to populate list
    await act(async () => {
      await result.current.fetchNotes()
    })

    vi.mocked(api.put).mockResolvedValueOnce(updatedNote)

    await act(async () => {
      await result.current.updateNote('1', { title: 'Updated Note' })
    })

    expect(result.current.notes[0].title).toBe('Updated Note')
    expect(api.put).toHaveBeenCalledWith('/api/notes/1', { title: 'Updated Note' })
  })

  it('should delete note from list', async () => {
    const note: Note = {
      id: '1',
      user_id: 'user1',
      title: 'Test Note',
      content: 'Test content',
      folder_id: null,
      is_pinned: false,
      is_archived: false,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
      tags: [],
    }

    vi.mocked(api.delete).mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useNotes())

    // Set initial note
    await act(async () => {
      result.current.notes = [note]
    })

    await act(async () => {
      await result.current.deleteNote('1')
    })

    expect(result.current.notes).toEqual([])
    expect(api.delete).toHaveBeenCalledWith('/api/notes/1')
  })

  it('should move note to folder', async () => {
    const note: Note = {
      id: '1',
      user_id: 'user1',
      title: 'Test Note',
      content: 'Test content',
      folder_id: null,
      is_pinned: false,
      is_archived: false,
      tags: [],
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    const mockResponse: PaginatedResponse<Note> = {
      items: [note],
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useNotes())

    // Fetch to populate
    await act(async () => {
      await result.current.fetchNotes()
    })

    vi.mocked(api.put).mockResolvedValueOnce({
      ...note,
      folder_id: 'folder1',
    })

    await act(async () => {
      await result.current.moveNoteToFolder('1', 'folder1')
    })

    expect(result.current.notes[0].folder_id).toBe('folder1')
    expect(api.put).toHaveBeenCalledWith('/api/notes/1', { folder_id: 'folder1' })
  })

  it('should clear error on successful operations', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Fetch failed'))

    const { result } = renderHook(() => useNotes())

    await act(async () => {
      await result.current.fetchNotes()
    })

    expect(result.current.error).toBe('Fetch failed')

    // Successful fetch should clear error
    const mockResponse: PaginatedResponse<Note> = {
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    await act(async () => {
      await result.current.fetchNotes()
    })

    expect(result.current.error).toBeNull()
  })
})
