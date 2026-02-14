import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useFolders } from './use-folders'
import { api } from '@/lib/api'
import type { Folder, PaginatedResponse } from '@/lib/types'

vi.mocked(api.get).mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 })
vi.mocked(api.post).mockResolvedValue({} as Folder)
vi.mocked(api.put).mockResolvedValue({} as Folder)
vi.mocked(api.delete).mockResolvedValue(undefined)

describe('useFolders', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useFolders())

    expect(result.current.folders).toEqual([])
    expect(result.current.folderTree).toEqual([])
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should fetch folders', async () => {
    const mockFolders: Folder[] = [
      {
        id: '1',
        user_id: 'user1',
        name: 'Folder 1',
        parent_id: null,
        icon: null,
        created_at: '2026-02-15T00:00:00Z',
        updated_at: '2026-02-15T00:00:00Z',
      },
    ]

    const mockResponse: PaginatedResponse<Folder> = {
      items: mockFolders,
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    await act(async () => {
      await result.current.fetchFolders()
    })

    expect(result.current.folders).toEqual(mockFolders)
    expect(result.current.loading).toBe(false)
    expect(api.get).toHaveBeenCalledWith('/api/folders?limit=50&offset=0')
  })

  it('should build folder tree from flat list', async () => {
    const rootFolder: Folder = {
      id: '1',
      user_id: 'user1',
      name: 'Root',
      parent_id: null,
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    const childFolder: Folder = {
      id: '2',
      user_id: 'user1',
      name: 'Child',
      parent_id: '1',
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    const mockFolders: Folder[] = [rootFolder, childFolder]
    const mockResponse: PaginatedResponse<Folder> = {
      items: mockFolders,
      total: 2,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    await act(async () => {
      await result.current.fetchFolders()
    })

    expect(result.current.folderTree).toHaveLength(1)
    expect(result.current.folderTree[0].id).toBe('1')
    expect(result.current.folderTree[0].children).toHaveLength(1)
    expect(result.current.folderTree[0].children?.[0].id).toBe('2')
  })

  it('should handle orphaned folders (missing parent)', async () => {
    const rootFolder: Folder = {
      id: '1',
      user_id: 'user1',
      name: 'Root',
      parent_id: null,
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    const orphanFolder: Folder = {
      id: '3',
      user_id: 'user1',
      name: 'Orphan',
      parent_id: 'nonexistent',
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    const mockFolders: Folder[] = [rootFolder, orphanFolder]
    const mockResponse: PaginatedResponse<Folder> = {
      items: mockFolders,
      total: 2,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    await act(async () => {
      await result.current.fetchFolders()
    })

    // Orphaned folder should be treated as root
    const ids = result.current.folderTree.map(f => f.id)
    expect(ids).toContain('1')
    expect(ids).toContain('3')
  })

  it('should handle fetch error', async () => {
    const errorMessage = 'Failed to fetch folders'
    vi.mocked(api.get).mockRejectedValueOnce(new Error(errorMessage))

    const { result } = renderHook(() => useFolders())

    await act(async () => {
      await result.current.fetchFolders()
    })

    expect(result.current.error).toBe(errorMessage)
    expect(result.current.folders).toEqual([])
  })

  it('should create folder at root level', async () => {
    const newFolder: Folder = {
      id: '2',
      user_id: 'user1',
      name: 'New Folder',
      parent_id: null,
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    vi.mocked(api.post).mockResolvedValueOnce(newFolder)
    const mockResponse: PaginatedResponse<Folder> = {
      items: [newFolder],
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    let createdFolder: Folder | undefined
    await act(async () => {
      createdFolder = await result.current.createFolder('New Folder')
    })

    expect(createdFolder).toEqual(newFolder)
    expect(api.post).toHaveBeenCalledWith('/api/folders', {
      name: 'New Folder',
      parent_id: null,
    })
  })

  it('should create subfolder with parent', async () => {
    const newFolder: Folder = {
      id: '2',
      user_id: 'user1',
      name: 'Subfolder',
      parent_id: '1',
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    vi.mocked(api.post).mockResolvedValueOnce(newFolder)
    const mockResponse: PaginatedResponse<Folder> = {
      items: [newFolder],
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    let createdFolder: Folder | undefined
    await act(async () => {
      createdFolder = await result.current.createFolder('Subfolder', '1')
    })

    expect(createdFolder).toEqual(newFolder)
    expect(api.post).toHaveBeenCalledWith('/api/folders', {
      name: 'Subfolder',
      parent_id: '1',
    })
  })

  it('should throw error on create failure', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Create failed'))

    const { result } = renderHook(() => useFolders())

    let threwError = false
    try {
      await act(async () => {
        await result.current.createFolder('New Folder')
      })
    } catch (err) {
      threwError = true
    }

    expect(threwError).toBe(true)
  })

  it('should update folder name', async () => {
    const updatedFolder: Folder = {
      id: '1',
      user_id: 'user1',
      name: 'Updated Folder',
      parent_id: null,
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    vi.mocked(api.put).mockResolvedValueOnce(updatedFolder)
    const mockResponse: PaginatedResponse<Folder> = {
      items: [updatedFolder],
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    let returnedFolder: Folder | undefined
    await act(async () => {
      returnedFolder = await result.current.updateFolder('1', { name: 'Updated Folder' })
    })

    expect(returnedFolder).toEqual(updatedFolder)
    expect(api.put).toHaveBeenCalledWith('/api/folders/1', { name: 'Updated Folder' })
  })

  it('should move folder to different parent', async () => {
    const movedFolder: Folder = {
      id: '2',
      user_id: 'user1',
      name: 'Moved Folder',
      parent_id: '3',
      icon: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    }

    vi.mocked(api.put).mockResolvedValueOnce(movedFolder)
    const mockResponse: PaginatedResponse<Folder> = {
      items: [movedFolder],
      total: 1,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    let returnedFolder: Folder | undefined
    await act(async () => {
      returnedFolder = await result.current.updateFolder('2', { parent_id: '3' })
    })

    expect(returnedFolder?.parent_id).toBe('3')
    expect(api.put).toHaveBeenCalledWith('/api/folders/2', { parent_id: '3' })
  })

  it('should return null on update failure', async () => {
    vi.mocked(api.put).mockRejectedValueOnce(new Error('Update failed'))

    const { result } = renderHook(() => useFolders())

    let threwError = false
    try {
      await act(async () => {
        await result.current.updateFolder('1', { name: 'Updated' })
      })
    } catch (err) {
      threwError = true
    }

    expect(threwError).toBe(true)
  })

  it('should delete folder', async () => {
    vi.mocked(api.delete).mockResolvedValueOnce(undefined)
    const mockResponse: PaginatedResponse<Folder> = {
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useFolders())

    await act(async () => {
      await result.current.deleteFolder('1')
    })

    expect(api.delete).toHaveBeenCalledWith('/api/folders/1')
  })

  it('should handle delete error gracefully', async () => {
    vi.mocked(api.delete).mockRejectedValueOnce(new Error('Delete failed'))

    const { result } = renderHook(() => useFolders())

    // Should not throw, error is caught and stored
    await act(async () => {
      try {
        await result.current.deleteFolder('1')
      } catch {
        // Expected - deleteFolder doesn't catch errors
      }
    })

    // Error should be set
    expect(result.current.error).toBe('Delete failed')
  })

  it('should clear error on successful operations', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Fetch failed'))

    const { result } = renderHook(() => useFolders())

    await act(async () => {
      await result.current.fetchFolders()
    })

    expect(result.current.error).toBe('Fetch failed')

    const mockResponse: PaginatedResponse<Folder> = {
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    }
    vi.mocked(api.get).mockResolvedValueOnce(mockResponse)

    await act(async () => {
      await result.current.fetchFolders()
    })

    expect(result.current.error).toBeNull()
  })
})
