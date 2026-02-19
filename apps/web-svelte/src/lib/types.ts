// Shared TypeScript types matching FastAPI schemas

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface Folder {
  id: string
  user_id: string
  name: string
  parent_id: string | null
  icon: string | null
  created_at: string
  updated_at: string
  children?: Folder[]
}

export interface Tag {
  id: string
  user_id: string
  name: string
  color: string
  created_at: string
}

export interface Note {
  id: string
  user_id: string
  title: string
  content: string
  folder_id: string | null
  is_pinned: boolean
  is_archived: boolean
  is_shared?: boolean
  created_at: string
  updated_at: string
  tags: Tag[]
}

export interface Todo {
  id: string
  user_id: string
  title: string
  description: string | null
  is_completed: boolean
  completed_at: string | null
  deadline: string | null
  parent_id: string | null
  note_id: string | null
  priority: number
  sort_order: number
  reminder_at: string | null
  reminder_sent: boolean
  recurrence_type: string | null
  recurrence_interval: number | null
  recurrence_days: string | null
  recurrence_end_date: string | null
  recurrence_parent_id: string | null
  created_at: string
  updated_at: string
  children?: Todo[]
  tags: Tag[]
}

export interface TelegramStatus {
  is_linked: boolean
  is_enabled: boolean
  chat_id: string | null
  bot_linked_at: string | null
}

export interface ImageUploadResponse {
  id: string
  url: string
  filename: string
  content_type: string
  size: number
}
