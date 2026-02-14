// Shared TypeScript types matching FastAPI schemas

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

export interface Note {
  id: string
  user_id: string
  title: string
  content: string
  folder_id: string | null
  is_pinned: boolean
  is_archived: boolean
  created_at: string
  updated_at: string
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
  created_at: string
  updated_at: string
  children?: Todo[]
}

export interface TelegramStatus {
  is_linked: boolean
  is_enabled: boolean
  chat_id: string | null
  bot_linked_at: string | null
}
