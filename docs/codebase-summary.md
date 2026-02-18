# Codebase Summary

## Overview

NotesApp is a full-stack monorepo with ~90+ source files totaling ~8,000+ LOC. Built with Bun monorepo + Turborepo, FastAPI backend, SvelteKit primary frontend (in progress), Tauri desktop app (macOS), Next.js legacy frontend (deprecated). Includes PWA/offline support, tagging system, recurring todos, note export, passkey WebAuthn auth, and theme toggle.

## Directory Structure

```
notesapp/
├── backend/                          # FastAPI backend (Python 3.13)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, CORS, lifespan scheduler
│   │   ├── config.py                 # Pydantic Settings, env vars
│   │   ├── database.py               # SQLAlchemy async engine & session
│   │   ├── deps.py                   # JWT auth (HS256 passkey-backed)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User ORM model (WebAuthn)
│   │   │   ├── credential.py         # Passkey credential storage
│   │   │   ├── note.py               # Note ORM model (UUID PK, user_id FK, tags)
│   │   │   ├── todo.py               # Todo ORM (hierarchical, reminders, recurrence, tags)
│   │   │   ├── folder.py             # Folder ORM (self-referential)
│   │   │   ├── tag.py                # Tag ORM (with junction tables: note_tags, todo_tags)
│   │   │   └── telegram.py           # TelegramSettings ORM
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Passkey registration/auth schemas
│   │   │   ├── note.py               # Pydantic schemas (Create/Update/Response)
│   │   │   ├── todo.py
│   │   │   ├── folder.py
│   │   │   └── telegram.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # POST /register, /authenticate (WebAuthn)
│   │   │   ├── notes.py              # CRUD + filters
│   │   │   ├── images.py             # Upload/serve/delete images (AZD-63)
│   │   │   ├── folders.py            # CRUD
│   │   │   ├── todos.py              # CRUD + toggle
│   │   │   └── telegram.py           # Link/unlink/status/webhook
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── note_query_service.py # Query builder + full-text search (tsvector)
│   │   │   ├── todo_query_service.py # Query builder + toggle logic
│   │   │   ├── reminder_service.py   # Check & send reminders
│   │   │   ├── telegram_service.py   # Send messages, get bot username, todo commands
│   │   │   ├── tag_service.py        # Tag CRUD, filtering, validation
│   │   │   ├── note_export_service.py# Export notes (WeasyPrint with lazy import)
│   │   │   ├── recurrence_service.py # Generate recurring todo instances
│   │   │   └── minio_storage_service.py # Image upload/download/delete (AZD-63)
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── reminders.py          # APScheduler background job
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   ├── versions/
│   │   │   └── 20260213_*.py         # Initial schema migration (with auth tables)
│   │   └── alembic.ini
│   ├── Dockerfile
│   ├── pyproject.toml                # uv dependencies
│   └── .env.example
├── apps/web-svelte/                  # SvelteKit 2 frontend (PRIMARY)
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte        # Root layout (theme provider)
│   │   │   ├── +page.svelte          # Landing/public page
│   │   │   ├── login/+page.svelte    # WebAuthn passkey login
│   │   │   ├── signup/+page.svelte   # WebAuthn passkey registration
│   │   │   ├── offline/+page.svelte  # PWA fallback offline page
│   │   │   └── (app)/                # Protected route group
│   │   │       ├── +layout.svelte    # Sidebar + header
│   │   │       ├── notes/+page.svelte # Notes list + editor
│   │   │       ├── todos/+page.svelte # Todos with filters
│   │   │       └── settings/+page.svelte # Profile + Telegram link
│   │   ├── lib/
│   │   │   ├── stores/
│   │   │   │   ├── auth-store.svelte.ts       # Passkey auth state
│   │   │   │   ├── notes-store.svelte.ts      # CRUD + caching
│   │   │   │   ├── todos-store.svelte.ts      # CRUD + filters
│   │   │   │   ├── folders-store.svelte.ts    # Tree builder
│   │   │   │   ├── tags-store.svelte.ts       # CRUD + filtering
│   │   │   │   └── online-status.svelte.ts    # Connectivity state
│   │   │   ├── utils/
│   │   │   │   └── debounce.svelte.ts
│   │   │   ├── api.ts                # API client (Bearer auth)
│   │   │   ├── auth-api.ts           # Passkey/WebAuthn API
│   │   │   ├── services/
│   │   │   │   └── image-upload-service.ts # Image validation + upload (AZD-63)
│   │   │   ├── extensions/
│   │   │   │   └── codemirror-image-drop-extension.ts # Drag/drop/paste images (AZD-63)
│   │   │   ├── types.ts              # TypeScript interfaces
│   │   │   └── offline/
│   │   │       ├── indexed-db-client.ts       # IndexedDB wrapper
│   │   │       ├── indexed-db-notes.ts        # Notes store
│   │   │       ├── indexed-db-todos.ts        # Todos store
│   │   │       ├── indexed-db-folders.ts      # Folders store
│   │   │       ├── indexed-db-sync-queue.ts   # Sync queue
│   │   │       ├── offline-sync-engine.ts     # Sync logic
│   │   │       └── offline-types.ts           # TypeScript interfaces
│   │   ├── hooks.server.ts           # Server-side hooks
│   │   └── app.d.ts                  # TypeScript app types
│   ├── static/                       # Static assets
│   ├── .gitignore
│   ├── package.json
│   ├── svelte.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── apps/web/                         # Next.js 16 frontend (DEPRECATED)
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
│   │   │   └── [various React components]
│   │   ├── hooks/
│   │   │   └── [various React hooks]
│   │   ├── lib/
│   │   │   ├── api.ts                # ApiClient (Bearer auth)
│   │   │   ├── types.ts              # Shared TypeScript interfaces
│   │   │   └── offline/
│   │   │       └── [offline support modules]
│   │   ├── middleware.ts             # Session refresh + route protection
│   │   └── favicon.ico
│   ├── public/                       # Static assets
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── [config files]
├── docker-compose.yml                # Local dev: postgres + backend
├── bun.lockb                         # Bun lock file
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
| Backend Python | 34 | ~2,500 |
| SvelteKit Frontend (TS/Svelte) | 32 | ~3,000 |
| Next.js Frontend (TS/TSX, deprecated) | 35 | ~4,000 |
| Tests (Backend & Frontend) | 12 | ~800 |
| Config & Docs | 8 | ~200 |
| **Total** | **121** | **~10,500** |

*Note: Next.js app included for reference during migration. Will be removed in v1.0.*

## Backend Structure (Python)

### Configuration & Setup
- **config.py** (50 LOC): Pydantic Settings for DATABASE_URL, JWT_SECRET, WEBAUTHN_*, TELEGRAM_*, CORS_ORIGINS
- **database.py** (50 LOC): SQLAlchemy async engine, session factory, _ensure_async_url() URL normalization
- **deps.py** (90 LOC): JWT validation dependency (HS256 passkey-backed), get_current_user, get_db

### Models (SQLAlchemy ORM)
- **user.py** (60 LOC): User model for local auth
- **credential.py** (80 LOC): Passkey credential storage (WebAuthn challenges, public keys)
- **note.py** (80 LOC): Note model, relationships to Folder, Todos, Tags
- **todo.py** (160 LOC): Todo model with hierarchy, reminders, recurrence fields, tags
- **folder.py** (75 LOC): Folder model with self-referential hierarchy
- **tag.py** (110 LOC): Tag model with junction tables (NoteTag, TodoTag)
- **telegram.py** (50 LOC): TelegramSettings per-user config

### Schemas (Pydantic)
- Separate schemas for each model: Create, Update, Response variants
- Automatic OpenAPI doc generation via FastAPI

### Routers (API Endpoints)
- **auth.py** (80 LOC): POST /register (WebAuthn), POST /authenticate (WebAuthn), GET /me
- **notes.py** (100 LOC): CRUD endpoints, filter by folder/archive/pinned/search
- **images.py** (136 LOC): POST upload, GET serve, DELETE, GET list (AZD-63)
- **folders.py** (80 LOC): CRUD endpoints
- **todos.py** (120 LOC): CRUD, toggle completion, filter by status/priority
- **telegram.py** (180 LOC): Link, unlink, status, webhook + command handlers

### Services (Business Logic)
- **note_query_service.py** (70 LOC): Dynamic query builder + PostgreSQL full-text search
- **todo_query_service.py** (70 LOC): Query builder + toggle logic + tag filtering
- **reminder_service.py** (50 LOC): Check pending reminders, mark sent
- **telegram_service.py** (50 LOC): Send messages, todo commands (/todo, /list, /done)
- **tag_service.py** (100 LOC): Tag CRUD, bulk assign/remove, validation
- **note_export_service.py** (160 LOC): Export to Markdown, PDF, ZIP (WeasyPrint with lazy import)
- **recurrence_service.py** (120 LOC): Generate todo instances from recurrence rules
- **minio_storage_service.py** (157 LOC): Upload/download/delete images to MinIO (AZD-63)

### Background Tasks
- **reminders.py** (60 LOC): APScheduler job to check & send reminders every 60s

### Entry Point
- **main.py** (66 LOC): FastAPI app, CORS middleware, lifespan context, router registration

## Frontend Structure - SvelteKit 2 (Primary)

### Pages (SvelteKit Routes)
- **routes/+layout.svelte** (root): Theme provider, global auth state
- **routes/+page.svelte**: Public landing page
- **routes/login/+page.svelte** (100 LOC): WebAuthn passkey authentication
- **routes/signup/+page.svelte** (120 LOC): WebAuthn passkey registration with display name
- **routes/(app)/+layout.svelte** (180 LOC): Protected layout with sidebar & header
- **routes/(app)/notes/+page.svelte** (180 LOC): Notes list + editor (pinned section)
- **routes/(app)/todos/+page.svelte** (160 LOC): Todos list with filters & recurrence
- **routes/(app)/settings/+page.svelte** (140 LOC): User profile, Telegram link, theme selector
- **routes/offline/+page.svelte**: PWA fallback offline page

### Svelte Stores (Reactive State)
- **auth-store.svelte.ts** (80 LOC): Passkey auth state, user identity
- **notes-store.svelte.ts** (150 LOC): CRUD, optimistic updates, caching, tag filtering
- **todos-store.svelte.ts** (140 LOC): CRUD, filtering by status/priority, recurrence info
- **folders-store.svelte.ts** (120 LOC): Folder CRUD, tree building, parentage
- **tags-store.svelte.ts** (100 LOC): Tag CRUD, filtering, color management
- **online-status.svelte.ts** (30 LOC): Connectivity state detection

### Lib & Utilities
- **api.ts** (70 LOC): API client (Bearer auth, error handling)
- **auth-api.ts** (80 LOC): WebAuthn/Passkey API calls
- **services/image-upload-service.ts** (80 LOC): Image validation, upload, error handling (AZD-63)
- **extensions/codemirror-image-drop-extension.ts** (139 LOC): Drag/drop/paste image integration (AZD-63)
- **types.ts** (50 LOC): TypeScript interfaces (Note, Todo, Folder, etc.)
- **utils/debounce.svelte.ts** (20 LOC): Debounce utility

### Offline Support
- **offline/indexed-db-client.ts** (60 LOC): IndexedDB wrapper
- **offline/indexed-db-notes.ts** (70 LOC): Notes persistence
- **offline/indexed-db-todos.ts** (70 LOC): Todos persistence
- **offline/indexed-db-folders.ts** (50 LOC): Folders persistence
- **offline/indexed-db-sync-queue.ts** (60 LOC): Pending operations queue
- **offline/offline-sync-engine.ts** (100 LOC): Sync logic (offline→online)
- **offline/offline-types.ts** (30 LOC): TypeScript interfaces

### Styling
- **globals.css** (100 LOC): TailwindCSS v4 @theme inline, dark/light/system modes
- **svelte.config.js**: SvelteKit adapter, preprocessor config
- **tailwind.config.ts**: Theme color overrides

## Frontend Structure - Next.js (Legacy/Deprecated)

> **Deprecated**: Kept for reference only. To be removed in v1.0. See SvelteKit app above for current implementation.

### Pages (Next.js App Router)
- Login/signup (Supabase auth, outdated)
- Notes/todos/settings (React components with hooks)

### Hooks (React)
- **use-auth.ts**: Supabase session (deprecated)
- **use-notes.ts**: CRUD operations
- **use-todos.ts**: CRUD, filtering
- **use-folders.ts**: Tree building
- Various other hooks

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

## Authentication Flow (Passkey WebAuthn)

**Registration:**
1. User enters display name on SvelteKit /signup
2. Frontend calls auth-api.registerPasskey() (WebAuthn)
3. Browser prompts for passkey creation (Face ID, Touch ID, PIN, etc.)
4. Backend stores credential in credentials table
5. Backend issues HS256 JWT session token
6. Frontend stores token in HttpOnly cookie + localStorage fallback

**Login:**
1. User navigates to SvelteKit /login
2. Frontend calls auth-api.authenticatePasskey() (WebAuthn)
3. Browser prompts for passkey authentication
4. Backend verifies challenge response
5. Backend issues HS256 JWT session token
6. Frontend stores token in HttpOnly cookie
7. User redirected to /notes (protected route)

**API Calls:**
1. All requests include Authorization: Bearer header (or via HttpOnly cookie)
2. Backend validates JWT signature using JWT_SECRET
3. Check expiry (default 7 days)
4. Extract user_id from sub claim
5. Proceed with user context

**Logout:**
1. Frontend clears HttpOnly cookie
2. User redirected to /

## Deployment Architecture

### Local Development
- Docker Compose: PostgreSQL (5432) + FastAPI (8000)
- bun run dev: Turborepo runs all dev servers
- Hot reload: Backend (uvicorn --reload), Frontend (SvelteKit Vite HMR)
- bun run dev:web-svelte: SvelteKit frontend only on port 5173

### Production (Planned)
- Backend: Containerized FastAPI on VPS/serverless
- Frontend (SvelteKit): Build to static + SSR on Node.js adapter or static CDN
- Database: PostgreSQL (local VPS or managed)
- CDN: CloudFront or similar for assets

## Dependencies Summary

### Backend (pyproject.toml)
- fastapi, uvicorn (web framework)
- sqlalchemy[asyncio], asyncpg (async ORM)
- pydantic-settings (config management)
- pyjwt[crypto] (HS256 JWT validation for passkey auth)
- webauthn (WebAuthn/FIDO2 support)
- apscheduler (background tasks)
- python-multipart (form data)
- alembic (migrations)
- weasyprint (PDF export, lazy imported)

### Frontend - SvelteKit (package.json)
- svelte 5, sveltekit 2 (framework)
- vite (build tool)
- typescript (type safety)
- tailwindcss 4 (styling)
- @simplewebauthn/browser (WebAuthn/passkey UI)
- codemirror (code editor)
- lucide-svelte (icons)
- date-fns (date utilities)
- vitest (testing)

### Frontend - Next.js (Legacy, package.json)
- next 16.1.6, react 19.2.3 (framework)
- @supabase/ssr, @supabase/supabase-js (deprecated)
- @uiw/react-codemirror (code editor)
- lucide-react (icons)
- react-markdown, remark-gfm (markdown)
- date-fns (date utilities)
- tailwindcss 4 (styling)

## Testing & Quality

- **Backend**: pytest with 22+ tests, GitHub Actions CI
- **Frontend**: vitest setup with test files for hooks, components
- **Linting**: ESLint (frontend), black (backend)
- **Type checking**: TypeScript strict mode, mypy (backend)
- **Coverage**: Aiming for 80%+ (in progress)

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

- Limited test coverage (expanding)
- No comprehensive error logging/monitoring
- Reminder service runs in-process (no distributed queue)
- No query result caching (Redis) - opportunity for performance
- No user profile customization beyond Telegram link
- Single-process recurrence generator (no distributed scheduling)
