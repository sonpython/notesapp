# System Architecture

## High-Level Overview

NotesApp is a three-tier full-stack application with multi-frontend support, including an MCP (Model Context Protocol) server for AI agent integration:

```
┌────────────────────────────────────────────────────────────────────┐
│                      CLIENT TIER                                   │
│  Primary: SvelteKit 2 (Svelte 5) - TailwindCSS v4                 │
│  Legacy: Next.js 16 (React 19) - TailwindCSS v4 (deprecated)      │
│  Service Worker (PWA), IndexedDB (offline), Theme toggle          │
│  SSR (SvelteKit) / SSR+RSC (Next.js), serves static assets        │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTPS/REST API (online)
                         │ Bearer JWT (HS256 passkey-backed)
                         │ Offline sync queue
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION TIER                           │
│  FastAPI - SQLAlchemy async - asyncpg                       │
│  Async request handlers, business logic, DB access          │
│  APScheduler background tasks, rate limiting (slowapi)      │
│  Pagination: limit/offset on list endpoints                 │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL / asyncpg
                         │ Session pool
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA TIER                                 │
│  PostgreSQL 16 (Local/Managed)                              │
│  Tables: notes, todos, folders, tags, note_tags, todo_tags │
│          telegram_settings, todo_folders                      │
│  Indexes: user_id, created_at, tag searches, reminders      │
│                                                              │
│  MinIO (S3-compatible object storage)                       │
│  Bucket: notesapp-images                                    │
│  Objects: users/{user_id}/images/{uuid}.{ext}              │
│  Allowed types: png, jpeg, gif, webp, svg, heic, heif, tiff│
└─────────────────────────────────────────────────────────────┘
```

> **Related:** See [data-flows-and-deployment.md](./data-flows-and-deployment.md) for data flow diagrams, deployment architecture, and operational details.

## Component Architecture

### Frontend (SvelteKit 2 - Primary)

> **Status**: Phases 1-3 migration complete. Svelte stores + routes match Next.js feature parity.

```
routes/
├── +layout.svelte (root)
│   └── Theme provider + auth state
├── +page.svelte (/)
│   └── Landing/public page
├── login/+page.svelte
│   └── WebAuthn passkey login
├── signup/+page.svelte
│   └── WebAuthn passkey registration
└── (app)/ [Protected routes]
   ├── +layout.svelte
   │   ├── AppSidebar (navigation + folder tree + user menu + theme toggle)
   │   ├── AppHeader (mobile hamburger + offline indicator)
   │   └── ThemeProvider (light/dark/system)
   ├── notes/+page.svelte
   │   ├── NoteList (cards + pinned section, tag filtering)
   │   ├── NoteEditor (CodeMirror + toolbar + image upload + export menu)
   │   └── NoteExportMenu (Markdown, PDF, ZIP export)
   ├── todos/+page.svelte
   │   ├── TodoList (recursive, tag filtering, recurrence badge)
   │   └── TodoCreateForm (with recurrence options)
   └── settings/+page.svelte
       ├── Theme preference selector
       ├── PWA install prompt
       └── Telegram link status & user profile

lib/
├── stores/ (Svelte stores)
│   ├── auth-store.svelte.ts (passkey auth state)
│   ├── notes-store.svelte.ts (CRUD + caching)
│   ├── todos-store.svelte.ts (CRUD + filters)
│   ├── folders-store.svelte.ts (tree builder)
│   ├── tags-store.svelte.ts (CRUD + filtering)
│   └── online-status.svelte.ts (connectivity state)
│
├── services/
│   └── image-upload-service.ts (validation + upload)
│
├── extensions/
│   └── codemirror-image-drop-extension.ts (drag/drop/paste images)
│
├── api.ts (API client with Bearer auth)
├── auth-api.ts (Passkey/WebAuthn API)
├── types.ts (TypeScript interfaces)
│
└── offline/
   ├── indexed-db-client.ts (IndexedDB wrapper)
   ├── indexed-db-notes.ts (Notes store)
   ├── indexed-db-todos.ts (Todos store)
   ├── indexed-db-folders.ts (Folders store)
   ├── indexed-db-sync-queue.ts (Pending ops)
   ├── offline-sync-engine.ts (Offline↔online sync)
   └── offline-types.ts (TypeScript interfaces)
```

### Frontend (Next.js App Router - Legacy)

> **Status**: Deprecated. Kept for reference during SvelteKit migration. Will be removed in v1.0.

### Backend Layered Architecture

```
FastAPI App (main.py)
│
├─ CORS Middleware
├─ Request Logger
└─ Routers
   ├─ /auth → auth.py
   │  └─ get_current_user (JWT validation)
   ├─ /notes → notes.py
   │  ├─ get_notes (filters: folder, archive, search)
   │  ├─ create_note
   │  ├─ update_note
   │  └─ delete_note
   ├─ /images → images.py
   │  ├─ POST /upload/ (multipart, 10MB max, 8 MIME types)
   │  ├─ GET /{id}/ (serve via proxy with auth)
   │  ├─ DELETE /{id}/
   │  └─ GET / (list user's images)
   ├─ /folders → folders.py
   │  ├─ CRUD endpoints (note folders)
   │  └─ Nested folder support
   ├─ /todo-folders → todo_folders.py (NEW)
   │  ├─ GET / (list folders, paginated)
   │  ├─ POST / (create folder)
   │  ├─ PUT /{id} (update folder)
   │  ├─ DELETE /{id} (delete folder)
   │  └─ GET /{id}/stats (completion stats)
   ├─ /todos → todos.py
   │  ├─ CRUD endpoints (with folder_id support)
   │  ├─ toggle_todo (completion)
   │  └─ Filter by folder
   └─ /telegram → telegram.py
      ├─ link/unlink endpoints
      ├─ status endpoint
      ├─ webhook handler
      └─ command handlers (/todo, /list, /done)

Each Router calls:
├─ Services (business logic)
│  ├─ note_query_service.py (full-text search: tsvector/tsquery)
│  ├─ todo_query_service.py
│  ├─ reminder_service.py
│  ├─ telegram_service.py (todo commands)
│  └─ minio_storage_service.py (image upload/download/delete)
├─ Schemas (validation)
│  └─ Pydantic models
└─ Models (ORM)
   ├─ Note (SQLAlchemy)
   ├─ Todo
   ├─ Folder (self-referential)
   └─ TelegramSettings

Background Tasks:
└─ APScheduler Job
   └─ reminders.py (check & send every 60s)
```

## Data Model Relationships

```
┌──────────────────────┐
│   users              │  (Local auth)
│ ├─ id (UUID, PK)     │
│ └─ display_name      │
└───────┬──────────────┘
        │ (user_id FK)
        │
        ├──────────────────────────────────────────┐
        │                                           │
        ▼                                           ▼
┌──────────────────────┐              ┌──────────────────────┐
│      notes           │              │   telegram_settings  │
├─ id (UUID, PK)      │              ├─ id (UUID, PK)       │
├─ user_id (FK)       │              ├─ user_id (FK, unique)│
├─ title              │              ├─ chat_id             │
├─ content            │              ├─ link_code           │
├─ folder_id (FK) ────┼──────┐       ├─ is_enabled          │
├─ is_pinned          │      │       └─ bot_linked_at       │
├─ is_archived        │      │
├─ created_at         │      │
└─ updated_at         │      │
    │                 │      │
    │ ┌─────────────┐ │      │
    │ │ note_tags   │ │      │
    │ │ (junction)  │ │      │
    │ └─────────────┘ │      │
    │       ▲          │      │
    │       └──────┐   │      │
    │              │   │      ▼
    │          ┌──────────────────────┐
    │          │     tags             │
    │          ├─ id (UUID, PK)       │
    │          ├─ user_id (FK)        │
    │          ├─ name (unique)       │
    │          ├─ color               │
    │          └─ created_at          │
    │              ▲                  │
    │              │                  │
    │          ┌──────────────────────┐
    │          │  todo_tags (junction)│
    │          └──────────────────────┘
    │              ▲
    │              │
        │       │
        │       ▼
        │   ┌──────────────────────┐
        │   │     folders          │
        │   ├─ id (UUID, PK)       │
        │   ├─ user_id (FK)        │
        │   ├─ name                │
        │   ├─ parent_id (FK) ────┐ Self-reference
        │   ├─ icon               │
        │   └─ created_at         │
        │   └─ updated_at         │
        └───────────────────────┘
        │
        ├──────────────────────────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────────────────┐  ┌──────────────────────┐
│       todos                      │  │   todos (child)      │
├─ id (UUID, PK)                  │  ├─ parent_id (FK) ────┐
├─ user_id (FK)                   │  │                      │
├─ title                          │  └─ Self-reference ────┘
├─ description                    │
├─ is_completed                   │
├─ completed_at                   │
├─ deadline                       │
├─ priority                       │
├─ parent_id (FK) ────┐           │
├─ note_id (FK) ──────┼──────────→ notes
├─ recurrence_type    │           │
├─ recurrence_interval│           │
├─ recurrence_days    │           │
├─ recurrence_end_date│           │
├─ recurrence_parent_id (FK) ─────┘
├─ folder_id (FK, nullable)  ────┐
├─ reminder_at                    │
├─ reminder_sent                  │
├─ created_at                     │
└─ updated_at                     │
        │
        ▼
┌──────────────────────────────┐
│     todo_folders             │  (NEW)
├─ id (UUID, PK)               │
├─ user_id (FK)                │
├─ name                         │
├─ parent_id (FK) ────────┐     │
├─ sort_order              │     │
├─ created_at              │     │
└─ updated_at              │     │
    (Self-reference) ──────┘
```

## MCP Server (AI Integration)

NotesApp includes a **FastMCP server** for Claude Desktop and AI agents to manage todos and folders programmatically.

### Architecture

```
Claude Desktop / AI Agent
        │
        ▼
┌───────────────────────┐
│   MCP Server (stdio)  │  (backend/mcp_server.py, 161 LOC)
│   - 10 tools         │
│   - Async support    │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────────────┐
│  MCP Services (mcp_todo_service) │
│  - list_todo_folders()         │
│  - create_todo_folder()        │
│  - update_todo_folder()        │
│  - delete_todo_folder()        │
│  - list_todos()                │
│  - create_todo()               │
│  - update_todo()               │
│  - delete_todo()               │
│  - toggle_todo()               │
│  - get_folder_stats()          │
└───────────┬───────────────────┘
            │
            ▼
    [Database Access]
    Same SQLAlchemy models + PostgreSQL
```

### Environment Variables

```env
NOTESAPP_USER_ID=<uuid>                    # User for MCP context
DATABASE_URL=postgresql+asyncpg://...      # PostgreSQL connection
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "notesapp-todos": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "/path/to/backend",
      "env": {
        "NOTESAPP_USER_ID": "<user-uuid>",
        "DATABASE_URL": "postgresql+asyncpg://..."
      }
    }
  }
}
```

### Supported Tools (10 total)

| Tool | Purpose | MCP Type |
|------|---------|----------|
| `list_todo_folders()` | Get all user todo folders | `call` |
| `create_todo_folder(name, parent_id?)` | Create new folder | `call` |
| `update_todo_folder(id, name, parent_id?)` | Update folder | `call` |
| `delete_todo_folder(id)` | Delete folder | `call` |
| `list_todos(folder_id?, is_completed?, limit)` | List todos with filters | `call` |
| `create_todo(title, folder_id?, priority, description?, deadline?, parent_id?)` | Create todo | `call` |
| `update_todo(id, title?, description?, priority?, folder_id?)` | Update todo | `call` |
| `delete_todo(id)` | Delete todo | `call` |
| `toggle_todo(id)` | Toggle completion | `call` |
| `get_folder_stats(folder_id)` | Get completion % | `call` |

---

## API Contract

### Request Pattern
```
GET /api/notes?folder_id=uuid&is_archived=false
Authorization: Bearer eyJxxx...
Content-Type: application/json
```

### Response Pattern
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "string",
    "content": "string",
    "folder_id": "uuid | null",
    "is_pinned": true|false,
    "is_archived": true|false,
    "created_at": "2024-02-14T10:00:00Z",
    "updated_at": "2024-02-14T10:00:00Z"
  }
]
```

### Image Upload Response Pattern
```json
{
  "id": "uuid",
  "filename": "screenshot.png",
  "size": 204800,
  "content_type": "image/png",
  "url": "/api/images/{id}"
}
```

### Error Pattern
```json
{
  "detail": "Note not found"
}
```

## Database Schema

### notes table
```sql
CREATE TABLE notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  title VARCHAR NOT NULL DEFAULT '',
  content TEXT NOT NULL DEFAULT '',
  folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
  is_pinned BOOLEAN NOT NULL DEFAULT false,
  is_archived BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  INDEX idx_notes_user_id (user_id),
  INDEX idx_notes_folder_id (folder_id)
);
```

### todos table
```sql
CREATE TABLE todos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  title VARCHAR NOT NULL,
  description TEXT,
  is_completed BOOLEAN NOT NULL DEFAULT false,
  completed_at TIMESTAMP WITH TIME ZONE,
  deadline TIMESTAMP WITH TIME ZONE,
  parent_id UUID REFERENCES todos(id) ON DELETE CASCADE,
  note_id UUID REFERENCES notes(id) ON DELETE SET NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  sort_order INTEGER NOT NULL DEFAULT 0,
  reminder_at TIMESTAMP WITH TIME ZONE,
  reminder_sent BOOLEAN NOT NULL DEFAULT false,
  recurrence_type VARCHAR(20),
  recurrence_interval INTEGER DEFAULT 1,
  recurrence_days VARCHAR(20),
  recurrence_end_date TIMESTAMP WITH TIME ZONE,
  recurrence_parent_id UUID REFERENCES todos(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  INDEX idx_todos_user_id (user_id),
  INDEX idx_todos_parent_id (parent_id),
  INDEX idx_todos_note_id (note_id),
  INDEX idx_todos_reminder_at (reminder_at, reminder_sent)
);
```

### folders table
```sql
CREATE TABLE folders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name VARCHAR NOT NULL,
  parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
  icon VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  INDEX idx_folders_user_id (user_id),
  INDEX idx_folders_parent_id (parent_id)
);
```

### tags & junction tables
```sql
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL DEFAULT '#6b7280',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  UNIQUE (user_id, name),
  INDEX idx_tags_user_id (user_id)
);

CREATE TABLE note_tags (
  note_id UUID PRIMARY KEY,
  tag_id UUID PRIMARY KEY,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE todo_tags (
  todo_id UUID PRIMARY KEY,
  tag_id UUID PRIMARY KEY,
  FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

### telegram_settings table
```sql
CREATE TABLE telegram_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  chat_id VARCHAR,
  is_enabled BOOLEAN NOT NULL DEFAULT true,
  link_code VARCHAR,
  bot_linked_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  INDEX idx_telegram_settings_user_id (user_id)
);
```

### todo_folders table (NEW)
```sql
CREATE TABLE todo_folders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name VARCHAR NOT NULL,
  parent_id UUID REFERENCES todo_folders(id) ON DELETE CASCADE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  INDEX idx_todo_folders_user_id (user_id),
  INDEX idx_todo_folders_parent_id (parent_id)
);

-- Todos table includes:
ALTER TABLE todos ADD COLUMN folder_id UUID REFERENCES todo_folders(id) ON DELETE SET NULL;
CREATE INDEX idx_todos_folder_id ON todos(folder_id);
```

## Authentication Architecture

### Passkey WebAuthn (Local HS256)

> **Note**: Migrated from Supabase to local passkey authentication.

### JWT Token Structure
```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "user-uuid",
  "iat": 1707900000,
  "exp": 1707903600,
  "user_id": "user-uuid"
}

Signature:
  HS256: signed with JWT_SECRET (env var, 64+ char random)
```

### Verification Flow
1. Client sends: Authorization: Bearer token (or via HttpOnly cookie)
2. Backend extracts token from header or cookie
3. Decode header to check algorithm (HS256 only)
4. Use local JWT_SECRET to validate signature
5. Check expiry (default 7 days)
6. Extract user_id from sub claim
7. Proceed with request in user context

### Passkey Registration & Login Flow
```
Registration:
1. User enters display name on /signup
2. Frontend calls auth-api.registerPasskey() (WebAuthn)
3. Browser shows passkey creation prompt (Face ID, Touch ID, PIN, etc.)
4. Backend stores credential in credentials table
5. Backend issues HS256 JWT session token
6. Frontend stores token in HttpOnly cookie

Login:
1. User navigates to /login
2. Frontend calls auth-api.authenticatePasskey() (WebAuthn)
3. Browser shows passkey authentication prompt
4. Backend verifies challenge response
5. Backend issues HS256 JWT session token
6. Frontend stores token in HttpOnly cookie
7. User redirected to /notes (protected route)
```

---

> **See also:** [data-flows-and-deployment.md](./data-flows-and-deployment.md) for data flow diagrams, PWA architecture, deployment, performance, scalability, and security details.
