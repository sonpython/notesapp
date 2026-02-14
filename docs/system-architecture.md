# System Architecture

## High-Level Overview

NotesApp is a three-tier full-stack application:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT TIER                            │
│  Next.js 16 (React 19) - TailwindCSS v4 - @supabase/ssr    │
│  Runs in browser & server (SSR), serves static assets       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/REST API
                         │ Bearer JWT
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION TIER                           │
│  FastAPI - SQLAlchemy async - asyncpg                       │
│  Async request handlers, business logic, DB access          │
│  APScheduler background tasks                               │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL / asyncpg
                         │ Session pool
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA TIER                                 │
│  PostgreSQL 16 - Supabase managed                           │
│  Tables: notes, todos, folders, telegram_settings           │
│  Indexes: user_id, created_at, updated_at                   │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend (Next.js App Router)

```
app/
├── layout.tsx (root)
│   └── Theme setup, fonts, dark mode
├── page.tsx (/)
│   └── Landing/public page
├── login, signup
│   └── Auth pages
└── (app)/ [Protected routes]
    ├── layout.tsx
    │   ├── AppSidebar (nav + folders + user menu)
    │   └── AppHeader (mobile hamburger)
    ├── notes/page.tsx
    │   ├── NoteList (cards + pinned section)
    │   └── NoteEditor (CodeMirror + toolbar)
    ├── todos/page.tsx
    │   ├── TodoList (recursive with subtasks)
    │   └── TodoCreateForm (quick input)
    └── settings/page.tsx
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
   │  ├─ get_notes (with filters)
   │  ├─ create_note
   │  ├─ update_note
   │  └─ delete_note
   ├─ /folders → folders.py
   ├─ /todos → todos.py
   │  └─ toggle_todo (completion)
   └─ /telegram → telegram.py
      ├─ webhook handler
      └─ link/unlink endpoints

Each Router calls:
├─ Services (business logic)
│  ├─ note_query_service.py
│  ├─ todo_query_service.py
│  ├─ reminder_service.py
│  └─ telegram_service.py
├─ Schemas (validation)
│  └─ Pydantic models
└─ Models (ORM)
   ├─ Note (SQLAlchemy)
   ├─ Todo
   ├─ Folder
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
        ├──────────────────────────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────┐            ┌──────────────────────┐
│      notes           │            │   telegram_settings  │
├─ id (UUID, PK)      │            ├─ id (UUID, PK)       │
├─ user_id (FK)       │            ├─ user_id (FK, unique)│
├─ title              │            ├─ chat_id             │
├─ content            │            ├─ link_code           │
├─ folder_id (FK) ────┼──────┐     ├─ is_enabled          │
├─ is_pinned          │      │     └─ bot_linked_at       │
├─ is_archived        │      │
├─ created_at         │      │
└─ updated_at         │      │
        │              │      │
        │              │      ▼
        │              │   ┌──────────────────────┐
        │              │   │     folders          │
        │              │   ├─ id (UUID, PK)      │
        │              │   ├─ user_id (FK)       │
        │              │   ├─ name               │
        │              │   ├─ parent_id (FK) ──┐ Self-reference
        │              │   ├─ icon              │
        │              │   └─ created_at        │
        │              │   └─ updated_at        │
        │              └───────────────────────┘
        │
        ├──────────────────────────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────┐            ┌──────────────────────┐
│       todos          │            │    todos (child)     │
├─ id (UUID, PK)      │            ├─ parent_id (FK) ────┐
├─ user_id (FK)       │            │                      │
├─ title              │            └─ Self-reference ────┘
├─ description        │
├─ is_completed       │
├─ completed_at       │
├─ deadline           │
├─ parent_id (FK) ────┼──────┐
├─ note_id (FK) ──────┼──────┼──→ notes
├─ priority           │      │
├─ reminder_at        │      │
├─ reminder_sent      │      │
└─ created_at         │      │
└─ updated_at         │      │
                      └──────┘
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

### JWT Token Structure (Supabase)
```
Header:
{
  "alg": "ES256",  (or HS256 for older projects)
  "typ": "JWT"
}

Payload:
{
  "sub": "user-uuid",
  "aud": "authenticated",
  "iat": 1707900000,
  "exp": 1707903600,
  "email": "user@example.com"
}

Signature:
{
  ES256: signed with Supabase private key
  HS256: signed with SUPABASE_JWT_SECRET
}
```

### Verification Flow
```
1. Client sends: Authorization: Bearer <token>
2. Backend extracts token from header
3. Decode header to check algorithm
4. If ES256/RS256: fetch public key from Supabase JWKS endpoint
5. If HS256: use local SUPABASE_JWT_SECRET
6. Validate signature
7. Check expiry (iat + exp)
8. Check audience (aud == "authenticated")
9. Extract user_id from sub claim
10. Proceed with request in user context
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
