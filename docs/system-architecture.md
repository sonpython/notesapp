# System Architecture

## High-Level Overview

NotesApp is a three-tier full-stack application with multi-frontend support:

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
│  PostgreSQL 16 - Supabase managed                           │
│  Tables: notes, todos, folders, tags, note_tags, todo_tags │
│          telegram_settings                                   │
│  Indexes: user_id, created_at, tag searches, reminders      │
└─────────────────────────────────────────────────────────────┘
```

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
   │   ├── NoteEditor (CodeMirror + toolbar + export menu)
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
│   ├── online-status.svelte.ts (connectivity state)
│
├── utils/
│   ├── debounce.svelte.ts
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

```
app/
├── layout.tsx (root)
│   └── Theme provider (light/dark/system), fonts, PWA setup
├── page.tsx (/)
│   └── Landing/public page
├── login, signup
│   └── Supabase auth pages (deprecated)
├── ~offline (PWA fallback page)
└── (app)/ [Protected routes]
    ├── layout.tsx
    │   ├── AppSidebar (navigation + folder tree + user menu + theme toggle)
    │   ├── AppHeader (mobile hamburger + offline indicator)
    │   └── OfflineIndicator (sync status badge)
    ├── notes/page.tsx
    │   ├── NoteList (cards + pinned section, tag filtering)
    │   ├── NoteEditor (CodeMirror + toolbar + export menu)
    │   ├── NoteExportMenu (Markdown, PDF, ZIP export)
    │   └── Search (300ms debounce, full-text search)
    ├── todos/page.tsx
    │   ├── TodoList (recursive, tag filtering, recurrence badge)
    │   └── TodoCreateForm (with recurrence options)
    └── settings/page.tsx
        ├── Theme preference selector
        ├── PWA install prompt
        └── Telegram link status & user profile
```

```
app/
├── layout.tsx (root)
│   └── Theme provider (light/dark/system), fonts, PWA setup
├── page.tsx (/)
│   └── Landing/public page
├── login, signup
│   └── Auth pages
├── ~offline (PWA fallback page)
└── (app)/ [Protected routes]
    ├── layout.tsx
    │   ├── AppSidebar (navigation + folder tree + user menu + theme toggle)
    │   ├── AppHeader (mobile hamburger + offline indicator)
    │   └── OfflineIndicator (sync status badge)
    ├── notes/page.tsx
    │   ├── NoteList (cards + pinned section, tag filtering)
    │   ├── NoteEditor (CodeMirror + toolbar + export menu)
    │   ├── NoteExportMenu (Markdown, PDF, ZIP export)
    │   └── Search (300ms debounce, full-text search)
    ├── todos/page.tsx
    │   ├── TodoList (recursive, tag filtering, recurrence badge)
    │   └── TodoCreateForm (with recurrence options)
    └── settings/page.tsx
        ├── Theme preference selector
        ├── PWA install prompt
        └── Telegram link status & user profile
```

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
   ├─ /folders → folders.py
   │  ├─ CRUD endpoints
   │  └─ Nested folder support
   ├─ /todos → todos.py
   │  ├─ CRUD endpoints
   │  └─ toggle_todo (completion)
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
│  └─ telegram_service.py (todo commands)
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

## Data Flow Diagrams

### Create Note Flow

```
User Action (Browser)
  │
  ├─> NoteEditor component
  │   └─ useNotes() hook
  │      └─ call api.post('/api/notes', { title, content })
  │
  ├─ API Client
  │  └─ fetch with Bearer token
  │
  ▼ HTTP Request

  /api/notes [POST]
  ├─ deps.get_current_user (JWT validation)
  │  └─ Extract user_id from token.sub
  │
  ├─ notes.py (router)
  │  └─ create_note_handler()
  │
  ├─ Schema validation (Pydantic)
  │  └─ CreateNoteRequest
  │
  ├─ Service layer (optional)
  │  └─ Some business logic
  │
  ├─ Model (ORM)
  │  └─ INSERT INTO notes (user_id, title, content, ...)
  │
  └─ Response
     └─ NoteResponse (id, user_id, title, created_at, ...)

Browser receives response
  │
  ├─ useNotes hook updates cache
  ├─ UI re-renders with new note
  └─ User sees note appear instantly (optimistic update)
```

### Todo Reminder Flow

```
Todo deadline approaching
  │
  ├─ APScheduler runs every 60s
  │  └─ tasks/reminders.py
  │     └─ check_pending_reminders()
  │
  ├─ Query database
  │  └─ SELECT * FROM todos
  │     WHERE reminder_at <= NOW()
  │     AND reminder_sent = false
  │     AND user_id = ?
  │
  ├─ For each pending reminder
  │  ├─ telegram_service.send_message()
  │  │  └─ HTTP POST to Telegram Bot API
  │  │
  │  └─ Mark as sent
  │     └─ UPDATE todos SET reminder_sent = true, updated_at = NOW()
  │
  └─ User receives Telegram notification
     └─ Chat notification on phone
```

### Full-Text Search Flow

```
User searches for notes
  │
  ├─ Frontend: notes/page.tsx
  │  └─ searchQuery state + useDebounce (300ms)
  │     └─ fetchNotes(folderId, debouncedSearch)
  │
  ▼ HTTP Request
  GET /api/notes?search=<query>&folder_id=<id>

Backend processing:
  │
  ├─ note_query_service.py
  │  └─ If search provided:
  │     ├─ Convert search to PostgreSQL plainto_tsquery
  │     ├─ Use to_tsvector() on notes.content
  │     └─ WHERE tsvector @@ tsquery
  │
  ├─ Query executes
  │  └─ SELECT * FROM notes WHERE user_id=? AND content_tsvector @@ tsquery
  │
  └─ Return matching notes with user_id filter

Frontend displays results
  └─ Real-time as user types (debounced)
```

### Folder Tree & Drag-Drop Flow

```
User clicks folder in tree or drags note to folder
  │
  ├─ Frontend: use-folders.ts hook
  │  ├─ getFolders() - fetch all user folders
  │  ├─ buildFolderTree() - parent_id -> child relationships
  │  └─ onDragDropNote() - move note to folder
  │
  ├─ FolderTreeItem component
  │  ├─ Expandable/collapsible (parent_id)
  │  ├─ Drag-drop enabled for notes
  │  └─ Context menu for CRUD
  │
  ▼ HTTP Request
  PUT /api/notes/<id> { folder_id: <target_folder_id> }

Backend:
  │
  ├─ notes.py router
  │  └─ update_note_handler()
  │     └─ UPDATE notes SET folder_id=?, updated_at=NOW()
  │
  └─ Return updated note

Frontend:
  └─ Optimistic UI update (instant feedback)
```

### Telegram Todo Commands Flow

```
User sends /todo Create project plan via Telegram
  │
  ├─ Telegram Bot API webhook receives message
  │  └─ POST /api/telegram/webhook
  │
  ├─ Backend parsing
  │  ├─ Extract chat_id
  │  ├─ Validate user (query telegram_settings by chat_id)
  │  └─ Extract command and args
  │
  ├─ Command handlers:
  │  ├─ /start <link_code> → _handle_start()
  │  │  └─ Link telegram account (store chat_id)
  │  ├─ /todo <title> → _handle_todo()
  │  │  └─ Create todo (INSERT todos)
  │  ├─ /list → _handle_list()
  │  │  └─ Query active todos (WHERE is_completed=false)
  │  └─ /done <n> → _handle_done()
  │     └─ Mark todo complete (UPDATE todos SET is_completed=true)
  │
  └─ Send Telegram response (confirmation or list)
     └─ User sees response in chat
```

### Authentication & Session Flow

```
User Signup/Login
  │
  ├─ Frontend
  │  └─ Supabase Auth
  │     └─ Email/password signup or login
  │
  ├─ Supabase
  │  └─ Validates credentials
  │  └─ Returns JWT (ES256 signed)
  │
  ├─ Frontend stores token
  │  └─ Secure httpOnly cookie (via @supabase/ssr)
  │  └─ localStorage backup
  │
  ├─ Middleware auto-refresh
  │  └─ Every request checks token expiry
  │  └─ Refreshes before 60 sec expiry
  │
  ├─ API call with Bearer token
  │  └─ Authorization: Bearer <jwt>
  │
  ├─ Backend JWT validation
  │  └─ deps.py get_current_user()
  │  ├─ Check token algorithm
  │  ├─ If ES256: use JWKS (public key from Supabase)
  │  ├─ If HS256: use JWT_SECRET
  │  └─ Extract user_id from sub claim
  │
  └─ Request proceeds with user context
     └─ All queries filtered by user_id
```

## Data Model Relationships

```
┌──────────────────────┐
│   auth.users         │  (Supabase managed)
│ ├─ id (UUID, PK)     │
│ └─ email             │
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
├─ reminder_at                    │
├─ reminder_sent                  │
├─ created_at                     │
└─ updated_at                     │
                                  │
    ┌─────────────────────────────┘
    │ (tags via todo_tags junction)
    ▼
  (tags table as above)
```

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

### Error Pattern
```json
{
  "detail": "Note not found"
}
```

## PWA & Offline Architecture

### Service Worker
- Caches static assets (JS, CSS, images) for offline access
- Network-first strategy: try online, fallback to cache
- Periodic sync for pending changes (when offline → online)

### IndexedDB Offline Storage
```
notes_store
  - pk: id (UUID)
  - notes: [{ id, title, content, folder_id, is_pinned, ... }]

todos_store
  - pk: id (UUID)
  - todos: [{ id, title, is_completed, deadline, ... }]

folders_store
  - pk: id (UUID)
  - folders: [{ id, name, parent_id, ... }]

sync_queue
  - pk: id (UUID)
  - pending: [{ type: 'create'|'update'|'delete', entity, timestamp }]
```

### Offline Sync Flow
1. User makes changes while offline
2. Changes stored in IndexedDB + added to sync_queue
3. Online status regained → offline-sync-engine triggers
4. Process sync_queue: retry failed ops, batch API calls
5. Remove synced items from queue, merge API responses
6. UI updates optimistically throughout

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
  -- Recurrence fields (AZD-18)
  recurrence_type VARCHAR(20),  -- 'daily', 'weekly', 'monthly', NULL=none
  recurrence_interval INTEGER DEFAULT 1,
  recurrence_days VARCHAR(20),  -- Weekday numbers or day of month
  recurrence_end_date TIMESTAMP WITH TIME ZONE,
  recurrence_parent_id UUID REFERENCES todos(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  INDEX idx_todos_user_id (user_id),
  INDEX idx_todos_parent_id (parent_id),
  INDEX idx_todos_note_id (note_id),
  INDEX idx_todos_reminder_at (reminder_at, reminder_sent),
  INDEX idx_todos_recurrence_parent_id (recurrence_parent_id)
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

### tags table (AZD-19)
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
```

### note_tags & todo_tags junction tables (AZD-19)
```sql
CREATE TABLE note_tags (
  note_id UUID PRIMARY KEY,
  tag_id UUID PRIMARY KEY,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
  INDEX idx_note_tags_tag_id (tag_id)
);

CREATE TABLE todo_tags (
  todo_id UUID PRIMARY KEY,
  tag_id UUID PRIMARY KEY,
  FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
  INDEX idx_todo_tags_tag_id (tag_id)
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

## Authentication Architecture

### Auth Migration: Passkey WebAuthn (Local)

> **Migration**: Changed from Supabase email/password to local passkey (WebAuthn/FIDO2).
> - No third-party auth provider
> - HS256 JWT issued by backend
> - Passkeys stored in database via SQLAlchemy

### JWT Token Structure (Local HS256)
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
{
  HS256: signed with JWT_SECRET (env var, 64+ char random)
}
```

### Verification Flow
```
1. Client sends: Authorization: Bearer <token> (or via HttpOnly cookie)
2. Backend extracts token from header or cookie
3. Decode header to check algorithm (HS256 only)
4. Use local JWT_SECRET to validate signature
5. Check expiry (iat + exp, default 7 days)
6. Extract user_id from sub claim
7. Proceed with request in user context

Note: Old Supabase ES256 tokens no longer accepted
```

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

Logout:
1. Frontend clears HttpOnly cookie
2. User redirected to /
```

## Background Task Scheduling

### APScheduler Configuration
```
Interval: Every 60 seconds
Task: check_pending_reminders()
Concurrency: Single process (no distribution)
Persistence: In-memory (lost on restart)
```

### Reminder Checking Logic
```
1. Query todos with reminder_at <= NOW() and reminder_sent = false
2. Filter by user_id (Supabase managed)
3. Check if Telegram linked for user
4. Send message to Telegram chat_id
5. Mark as sent: UPDATE todos SET reminder_sent = true
6. Log result (success/failure)
```

## Deployment Architecture (Production)

```
                    User Browser
                         │
                         ▼
                    ┌─────────────┐
                    │  Vercel/CDN │ (Static frontend)
                    │ (Next.js)   │
                    └──────┬──────┘
                           │ API calls
                           ▼
                    ┌────────────────┐
                    │  Load Balancer │ (nginx/AWS ALB)
                    └────────┬───────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      ┌─────────┐      ┌─────────┐      ┌─────────┐
      │ FastAPI │      │ FastAPI │      │ FastAPI │
      │  (Pod 1)│      │ (Pod 2) │      │  (Pod 3)│
      └────┬────┘      └────┬────┘      └────┬────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  Supabase        │
                   │ (Managed         │
                   │ PostgreSQL)      │
                   │ (Replication)    │
                   └──────────────────┘
```

## Performance Optimization Strategies

### Query Optimization
- Index user_id on all tables (fast filtering)
- Eager load related data (avoid N+1)
- Use connection pooling (Supabase session mode)
- Batch operations where possible

### Frontend Optimization
- Code splitting by route
- Lazy load components (React.lazy)
- Debounce auto-save (500ms)
- Optimistic UI updates (no wait for server)

### Caching Strategy (Future)
- Redis for session cache
- CDN for static assets
- Query result caching (1 hour)
- Browser cache headers

### Database Optimization (Future)
- Query result pagination
- Full-text search index
- Table partitioning (by user_id)
- Query analysis & query plans

## Scalability Considerations

### Horizontal Scaling
- Stateless FastAPI instances (no session affinity needed)
- Load balancer distributes requests
- Each instance connects to shared database

### Vertical Scaling
- Increase container memory (API)
- Increase database connection pool
- Upgrade PostgreSQL instance size (Supabase)

### Bottlenecks
- Database connection pool (currently: 5-20 connections)
- APScheduler runs in single process (no distributed scheduling)
- No caching layer (every read hits database)

## Security Architecture

### Data Isolation
- All queries filtered by user_id from JWT
- No cross-user data access possible
- Passwords managed by Supabase (not stored locally)

### Token Management
- JWT stored in secure httpOnly cookies
- Automatic refresh before expiry
- CORS restricts origin access
- CSRF protection via SameSite cookies

### Input Validation
- Pydantic validates all request bodies
- SQL injection prevented via ORM parameterization
- XSS prevented via React auto-escaping
- No eval/exec of user input

## Error Handling & Recovery

### API Error Response
```python
raise HTTPException(
  status_code=404,
  detail="Note not found"
)
```

### Frontend Error Recovery
```typescript
try {
  const note = await api.get(`/api/notes/${id}`)
} catch (error) {
  // Show toast notification
  // Retry after delay
  // Use stale cache if available
}
```

### Database Connection Recovery
- pool_pre_ping=True (detect dead connections)
- Auto-reconnect on failure
- Exponential backoff for retries

## Monitoring & Observability (Future)

### Metrics to Track
- API response time (p50, p95, p99)
- Error rate by endpoint
- Database query latency
- Cache hit rate
- Active user sessions

### Logging Strategy
- Structured JSON logs
- Log level: DEBUG, INFO, WARNING, ERROR
- Include request ID for tracing
- No sensitive data in logs

### Alerting (Future)
- Error rate threshold
- Response time degradation
- Database connection pool exhaustion
- Telegram API failures
