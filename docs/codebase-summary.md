# Codebase Summary

## Overview

NotesApp is a full-stack monorepo with ~56 source files (28 Python, 28 TypeScript/React) totaling ~4,900 LOC. Built with pnpm workspace + Turborepo, FastAPI backend, Next.js frontend.

## Directory Structure

```
notesapp/
├── backend/                          # FastAPI backend (Python 3.13)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, CORS, lifespan scheduler
│   │   ├── config.py                 # Pydantic Settings, env vars
│   │   ├── database.py               # SQLAlchemy async engine & session
│   │   ├── deps.py                   # JWT auth (ES256 JWKS + HS256)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── note.py               # Note ORM model (UUID PK, user_id FK)
│   │   │   ├── todo.py               # Todo ORM (hierarchical, reminders)
│   │   │   ├── folder.py             # Folder ORM (self-referential)
│   │   │   └── telegram.py           # TelegramSettings ORM
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── note.py               # Pydantic schemas (Create/Update/Response)
│   │   │   ├── todo.py
│   │   │   ├── folder.py
│   │   │   └── telegram.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # GET /me endpoint
│   │   │   ├── notes.py              # CRUD + filters
│   │   │   ├── folders.py            # CRUD
│   │   │   ├── todos.py              # CRUD + toggle
│   │   │   └── telegram.py           # Link/unlink/status/webhook
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── note_query_service.py # Query builder + full-text search (tsvector)
│   │   │   ├── todo_query_service.py # Query builder + toggle logic
│   │   │   ├── reminder_service.py   # Check & send reminders
│   │   │   └── telegram_service.py   # Send messages, get bot username, todo commands
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── reminders.py          # APScheduler background job
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   ├── versions/
│   │   │   └── 20260213_*.py         # Initial schema migration
│   │   └── alembic.ini
│   ├── Dockerfile
│   ├── pyproject.toml                # uv dependencies
│   └── .env.example
├── apps/web/                         # Next.js 16 frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx            # Root layout (dark theme)
│   │   │   ├── page.tsx              # Landing/public page
│   │   │   ├── login/page.tsx        # Login form
│   │   │   ├── signup/page.tsx       # Signup form
│   │   │   ├── globals.css           # TailwindCSS v4 @theme inline
│   │   │   └── (app)/                # Protected route group
│   │   │       ├── layout.tsx        # Sidebar + header
│   │   │       ├── notes/page.tsx    # 2-col notes UI
│   │   │       ├── todos/page.tsx    # Todos with filters
│   │   │       └── settings/page.tsx # Profile + Telegram link
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── app-header.tsx    # Mobile header
│   │   │   │   └── app-sidebar.tsx   # Nav + folders + user menu
│   │   │   ├── notes/
│   │   │   │   ├── note-editor.tsx   # CodeMirror + toolbar + autosave
│   │   │   │   ├── note-list.tsx     # Pinned/regular note cards
│   │   │   │   └── note-preview.tsx  # Markdown preview (react-markdown)
│   │   │   ├── todos/
│   │   │   │   ├── todo-item.tsx     # Recursive todo (subtasks)
│   │   │   │   ├── todo-list.tsx     # List container
│   │   │   │   └── todo-create-form.tsx # New todo input
│   │   │   └── folders/
│   │   │       ├── folder-tree.tsx        # Folder tree container
│   │   │       ├── folder-tree-item.tsx   # Expandable folder item
│   │   │       └── folder-context-menu.tsx # Create/rename/delete context menu
│   │   ├── hooks/
│   │   │   ├── use-auth.ts           # Supabase auth state
│   │   │   ├── use-debounce.ts       # Debounce hook
│   │   │   ├── use-notes.ts          # CRUD + optimistic updates
│   │   │   ├── use-todos.ts          # CRUD + filters
│   │   │   ├── use-telegram.ts       # Telegram link/status
│   │   │   └── use-folders.ts        # Folder CRUD + tree builder
│   │   ├── lib/
│   │   │   ├── api.ts                # ApiClient (Bearer auth)
│   │   │   ├── types.ts              # Shared TypeScript interfaces
│   │   │   ├── supabase-browser.ts   # Supabase client (browser)
│   │   │   └── supabase-server.ts    # Supabase client (server/middleware)
│   │   ├── middleware.ts             # Session refresh + route protection
│   │   └── favicon.ico
│   ├── public/                       # Static assets
│   ├── .gitignore
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   ├── postcss.config.mjs
│   └── tailwind.config.ts
├── docker-compose.yml                # Local dev: postgres + backend
├── pnpm-workspace.yaml               # Monorepo config
├── turbo.json                        # Turborepo task pipeline
├── package.json                      # Root workspace scripts
├── CLAUDE.md                         # Project instructions for Claude
├── README.md                         # Quick start guide
└── docs/                             # Documentation
    ├── project-overview-pdr.md
    ├── codebase-summary.md (this file)
    ├── code-standards.md
    ├── system-architecture.md
    ├── project-roadmap.md
    ├── deployment-guide.md
    └── design-guidelines.md
```

## File Count & LOC

| Category | Count | LOC (est) |
|----------|-------|----------|
| Backend Python | 28 | ~1,600 |
| Frontend TS/TSX | 28 | ~3,100 |
| Config & Docs | 8 | ~200 |
| **Total** | **64** | **~4,900** |

## Backend Structure (Python)

### Configuration & Setup
- **config.py** (46 LOC): Pydantic Settings for DATABASE_URL, SUPABASE_*, TELEGRAM_*, CORS_ORIGINS
- **database.py** (48 LOC): SQLAlchemy async engine, session factory, _ensure_async_url() URL normalization
- **deps.py** (88 LOC): JWT validation dependency (ES256 via JWKS + HS256), get_current_user, get_db

### Models (SQLAlchemy ORM)
- **note.py** (75 LOC): Note model, relationships to Folder & Todos
- **todo.py** (110 LOC): Todo model with parent-child hierarchy, reminder fields, note FK
- **folder.py** (75 LOC): Folder model with self-referential hierarchy
- **telegram.py** (50 LOC): TelegramSettings per-user config

### Schemas (Pydantic)
- Separate schemas for each model: Create, Update, Response variants
- Automatic OpenAPI doc generation via FastAPI

### Routers (API Endpoints)
- **auth.py** (30 LOC): GET /api/auth/me (user identity)
- **notes.py** (100 LOC): CRUD endpoints, filter by folder/archive/pinned
- **folders.py** (80 LOC): CRUD endpoints
- **todos.py** (120 LOC): CRUD, toggle completion, filter by status/priority
- **telegram.py** (180 LOC): Link, unlink, status, webhook + command handlers

### Services (Business Logic)
- **note_query_service.py** (70 LOC): Dynamic query builder + PostgreSQL full-text search
- **todo_query_service.py** (70 LOC): Query builder + toggle logic
- **reminder_service.py** (50 LOC): Check pending reminders, mark sent
- **telegram_service.py** (50 LOC): Send messages, todo commands (/todo, /list, /done)

### Background Tasks
- **reminders.py** (60 LOC): APScheduler job to check & send reminders every 60s

### Entry Point
- **main.py** (66 LOC): FastAPI app, CORS middleware, lifespan context, router registration

## Frontend Structure (React/Next.js)

### Pages (Next.js App Router)
- **layout.tsx** (root): Dark theme setup, fonts
- **page.tsx** (landing): Public landing page
- **login/page.tsx** (80 LOC): Email/password login form
- **signup/page.tsx** (90 LOC): User registration
- **(app)/layout.tsx** (200 LOC): Protected layout with sidebar & header
- **(app)/notes/page.tsx** (200 LOC): 2-column notes list + editor
- **(app)/todos/page.tsx** (150 LOC): Todo list with filters & creation
- **(app)/settings/page.tsx** (150 LOC): User profile & Telegram link status

### Components
- **app-header.tsx** (80 LOC): Mobile hamburger menu
- **app-sidebar.tsx** (150 LOC): Navigation, real folder tree, user menu
- **note-editor.tsx** (150 LOC): CodeMirror editor, toolbar, auto-save
- **note-list.tsx** (100 LOC): Note cards grid/list view
- **note-preview.tsx** (80 LOC): Markdown preview with react-markdown
- **todo-item.tsx** (150 LOC): Recursive todo renderer (subtasks)
- **todo-list.tsx** (100 LOC): Todo container with filter buttons
- **todo-create-form.tsx** (100 LOC): New todo input form
- **folder-tree.tsx** (128 LOC): Folder tree container with drag-drop
- **folder-tree-item.tsx** (213 LOC): Expandable folder with drag-drop
- **folder-context-menu.tsx** (84 LOC): Create/rename/delete menu

### Hooks
- **use-auth.ts** (50 LOC): Supabase session management
- **use-debounce.ts** (20 LOC): Debounce utility
- **use-notes.ts** (120 LOC): CRUD operations, optimistic updates, caching
- **use-todos.ts** (110 LOC): CRUD, filtering, completion toggle
- **use-telegram.ts** (80 LOC): Link/unlink/status operations
- **use-folders.ts** (131 LOC): Folder CRUD, tree building, parentage

### Lib & Utilities
- **api.ts** (60 LOC): ApiClient class (GET, POST, PUT, DELETE with auth headers)
- **types.ts** (50 LOC): TypeScript interfaces (Note, Todo, Folder, TelegramStatus)
- **supabase-browser.ts** (20 LOC): Browser-side Supabase client
- **supabase-server.ts** (20 LOC): Server-side Supabase client
- **middleware.ts** (50 LOC): Session refresh, route protection

### Styling
- **globals.css** (80 LOC): TailwindCSS v4 @theme inline, dark mode CSS variables
- **tailwind.config.ts**: Theme color overrides
- **postcss.config.mjs**: PostCSS processing

## Key Patterns

### Backend Patterns
- **Dependency Injection**: FastAPI Depends() for get_db, get_current_user
- **Async-First**: asyncio + asyncpg for database, async/await endpoints
- **Query Builders**: Service layer for complex WHERE clauses
- **Layered Architecture**: Routers → Services → Models
- **Type Safety**: Pydantic validation on all inputs
- **Error Handling**: HTTPException with appropriate status codes

### Frontend Patterns
- **Custom Hooks**: Encapsulate API calls & state logic
- **Optimistic Updates**: Update UI before API confirmation
- **Component Composition**: Small, reusable components
- **React Server Components** (Next.js): Server-side rendering where possible
- **Type Safety**: TypeScript interfaces for API responses
- **Debouncing**: 500ms debounce on auto-save to reduce API calls

### Database Patterns
- **User Isolation**: All queries filter by user_id
- **Soft Deletes**: is_archived flag (no hard deletion in production)
- **Cascading Deletes**: Folders & Todos auto-delete children
- **Timestamps**: created_at, updated_at on all tables
- **Indexing**: user_id indexed for fast lookups
- **Foreign Keys**: Enforce referential integrity

## Authentication Flow

1. Supabase Auth emits JWT (ES256 signed)
2. Next.js middleware refreshes before expiry
3. Token stored in httpOnly cookie
4. API calls include Authorization: Bearer header
5. Backend validates via JWKS endpoint
6. User ID extracted from sub claim

## Deployment Architecture

### Local Development
- Docker Compose: PostgreSQL (5432) + FastAPI (8000)
- pnpm dev: Turborepo runs all dev servers
- Hot reload: Backend (uvicorn --reload), Frontend (Next.js HMR)

### Production (Planned)
- Backend: Containerized FastAPI on VPS/serverless
- Frontend: Static build deployed to Vercel or VPS
- Database: Managed PostgreSQL (Supabase)
- CDN: CloudFront or similar for assets

## Dependencies Summary

### Backend (pyproject.toml)
- fastapi, uvicorn (web framework)
- sqlalchemy[asyncio], asyncpg (async ORM)
- pydantic-settings (config management)
- python-jose[cryptography], pyjwt (JWT)
- apscheduler (background tasks)
- python-multipart (form data)
- alembic (migrations)

### Frontend (package.json)
- next 16.1.6, react 19.2.3 (framework)
- @supabase/ssr, @supabase/supabase-js (auth + DB)
- @uiw/react-codemirror (code editor)
- lucide-react (icons)
- react-markdown, remark-gfm (markdown)
- date-fns (date utilities)
- tailwindcss 4 (styling)

## Testing & Quality

- **No unit tests** currently (gap identified)
- **No CI/CD pipeline** (manual testing only)
- **Linting**: ESLint (frontend), black (backend, manual)
- **Type checking**: TypeScript strict mode, mypy (backend, manual)

## Performance Characteristics

- **API Response**: ~50-100ms (local), ~150-200ms (network)
- **Page Load**: ~1.5s (initial), ~300ms (navigation)
- **Auto-save Latency**: ~600ms (500ms debounce + request)
- **Database Queries**: < 10ms (indexed user_id)
- **Connection Pool**: 5-20 connections (tunable)

## Scalability Considerations

- **Stateless**: FastAPI backend can scale horizontally
- **Connection Pooling**: Supabase session mode handles 10k+ concurrent connections
- **Caching**: None currently (opportunity for Redis)
- **CDN**: Static assets not CDN'd (production optimization)
- **Distributed Scheduling**: APScheduler runs single-process (no clustering)

## Known Technical Debt

- No offline-first PWA
- No test suite
- No comprehensive error logging
- Reminder service runs in-process (no external queue)
- No pagination on large result sets
- No query result caching (Redis)
