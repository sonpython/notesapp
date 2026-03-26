# NotesApp

A modern, full-stack note-taking and todo management application with Telegram reminder integration.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.13 (via `uv`)
- Node.js 22+
- Bun 1.2.4+

### Local Development

```bash
# Install dependencies
bun install

# Set up environment
cp backend/.env.example backend/.env
cp apps/web-svelte/.env.example apps/web-svelte/.env.local

# Start database & backend
docker-compose up -d

# Run database migrations (first time only)
cd backend && alembic upgrade head && cd ..

# Start dev servers
bun run dev
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432

### Development Commands

```bash
bun run dev              # Run all services in dev mode
bun run build            # Build frontend and backend
bun run lint             # Lint all packages
bun run dev:web-svelte   # SvelteKit frontend
bun run build:web-svelte # Build SvelteKit frontend
bun run dev:desktop      # Tauri desktop app
bun run build:desktop    # Build Tauri desktop app
```

## Architecture Overview

### Stack
- **Backend**: FastAPI + SQLAlchemy async + asyncpg + Alembic (Python 3.13)
- **Frontend (Primary)**: SvelteKit 2 + Svelte 5 + TailwindCSS v4 (in progress, Phases 1-3 done)
- **Desktop**: Tauri v2 (macOS, Phases 1-2 done)
- **Frontend (Legacy)**: Next.js 16 (deprecated, kept for reference)
- **Database**: PostgreSQL (local or managed)
- **Storage**: MinIO (S3-compatible object storage for images)
- **Auth**: Passkey-only (WebAuthn/FIDO2) with local HS256 JWT sessions
- **Infrastructure**: Bun monorepo + Turborepo, Docker Compose

### Key Features
- **Notes**: Rich text editing (CodeMirror), auto-save with debounce, pinned/archived states, folder organization, image uploads
- **Todos**: Hierarchical todos with subtasks, priority levels, deadlines, separate folder organization, completion % tracking
- **Todo Folders**: Nested hierarchy for todo organization, independent from note folders, completion stats
- **Images**: Drag-drop/paste image uploads in notes, MinIO backend storage, 10MB file size limit
- **Folders**: Nested folder hierarchy for note organization
- **Telegram**: Direct reminder delivery via Telegram bot, per-user link code pairing
- **MCP Server**: AI agent integration via Model Context Protocol (Claude Desktop, stdio transport)
- **Auth**: Passkey-only (WebAuthn/FIDO2) with local HS256 JWT sessions

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, scheduler
│   │   ├── config.py            # Settings from .env (JWT_SECRET, WEBAUTHN_*)
│   │   ├── database.py          # SQLAlchemy async engine & session
│   │   ├── deps.py              # JWT auth dependency (HS256)
│   │   ├── models/              # SQLAlchemy ORM models (+ user, credential for auth)
│   │   ├── schemas/             # Pydantic request/response schemas (+ auth schemas)
│   │   ├── routers/             # API endpoints (+ /auth/register, /auth/authenticate)
│   │   ├── services/            # Business logic
│   │   └── tasks/               # Background jobs (APScheduler)
│   ├── alembic/                 # Database migrations
│   ├── Dockerfile               # Backend container
│   └── pyproject.toml           # Python dependencies (uv)
├── apps/web-svelte/             # SvelteKit 2 frontend (PRIMARY)
│   ├── src/
│   │   ├── routes/              # SvelteKit routes (pages)
│   │   ├── lib/
│   │   │   ├── stores/          # Svelte reactive stores
│   │   │   ├── api.ts           # API client (Bearer auth)
│   │   │   ├── auth-api.ts      # WebAuthn/passkey API
│   │   │   ├── types.ts         # TypeScript interfaces
│   │   │   └── offline/         # IndexedDB + sync engine
│   │   ├── hooks.server.ts      # Server-side hooks
│   │   └── app.d.ts             # App types
│   ├── static/                  # Static assets
│   ├── package.json             # Node dependencies
│   ├── svelte.config.js         # SvelteKit config
│   └── vite.config.ts           # Vite config
├── apps/desktop/                # Tauri v2 desktop app (macOS)
│   ├── src/                     # Svelte UI
│   ├── src-tauri/               # Rust backend
│   ├── package.json             # Node dependencies
│   └── [Tauri config]
├── apps/web/                    # Next.js 16 frontend (DEPRECATED - for reference)
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom React hooks (deprecated)
│   │   └── lib/                 # Utilities
│   ├── package.json             # Node dependencies
│   └── [config files]
├── docker-compose.yml           # Local dev environment
├── bun.lockb                    # Bun lock file
├── turbo.json                   # Turborepo config
└── docs/                        # Documentation
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | No | Health check |
| GET | `/api/auth/me` | Yes | Current user info |
| GET | `/api/notes` | Yes | List notes with filters |
| POST | `/api/notes` | Yes | Create note |
| GET | `/api/notes/{id}` | Yes | Get note |
| PUT | `/api/notes/{id}` | Yes | Update note |
| DELETE | `/api/notes/{id}` | Yes | Delete note |
| GET | `/api/folders` | Yes | List folders |
| POST | `/api/folders` | Yes | Create folder |
| PUT | `/api/folders/{id}` | Yes | Update folder |
| DELETE | `/api/folders/{id}` | Yes | Delete folder |
| GET | `/api/todos` | Yes | List todos with filters |
| POST | `/api/todos` | Yes | Create todo |
| GET | `/api/todos/{id}` | Yes | Get todo |
| PUT | `/api/todos/{id}` | Yes | Update todo |
| DELETE | `/api/todos/{id}` | Yes | Delete todo |
| POST | `/api/todos/{id}/toggle` | Yes | Toggle todo completion |
| GET | `/api/todo-folders` | Yes | List todo folders (paginated) |
| POST | `/api/todo-folders` | Yes | Create todo folder |
| PUT | `/api/todo-folders/{id}` | Yes | Update todo folder |
| DELETE | `/api/todo-folders/{id}` | Yes | Delete todo folder |
| GET | `/api/todo-folders/{id}/stats` | Yes | Get folder completion stats |
| POST | `/api/images/upload` | Yes | Upload image (multipart, 10MB max) |
| GET | `/api/images/{id}` | Yes | Serve image via proxy (cache: 1 day) |
| DELETE | `/api/images/{id}` | Yes | Delete image |
| GET | `/api/images` | Yes | List user images |
| GET | `/api/telegram/status` | Yes | Get Telegram link status |
| POST | `/api/telegram/link` | Yes | Generate link code |
| POST | `/api/telegram/unlink` | Yes | Unlink Telegram |
| POST | `/api/telegram/webhook` | No | Telegram webhook handler |

## Data Models

### Note
```
id: UUID (PK)
user_id: UUID (from auth.users)
title: string
content: text
folder_id: UUID (FK, nullable)
is_pinned: boolean
is_archived: boolean
created_at: datetime
updated_at: datetime
```

### Todo
```
id: UUID (PK)
user_id: UUID (from auth.users)
title: string
description: text (nullable)
is_completed: boolean
completed_at: datetime (nullable)
deadline: datetime (nullable)
parent_id: UUID (FK to todos, nullable)
folder_id: UUID (FK to todo_folders, nullable)
note_id: UUID (FK to notes, nullable)
priority: int (0=none, 1=low, 2=medium, 3=high)
sort_order: int
reminder_at: datetime (nullable)
reminder_sent: boolean
created_at: datetime
updated_at: datetime
```

### TodoFolder
```
id: UUID (PK)
user_id: UUID (from auth.users)
name: string
parent_id: UUID (FK to todo_folders, nullable)
sort_order: int
created_at: datetime
updated_at: datetime
```

### Folder
```
id: UUID (PK)
user_id: UUID (from auth.users)
name: string
parent_id: UUID (FK to folders, nullable)
icon: string (nullable)
created_at: datetime
updated_at: datetime
```

### TelegramSettings
```
id: UUID (PK)
user_id: UUID (from auth.users, unique)
chat_id: string (nullable)
is_enabled: boolean
link_code: string (nullable)
bot_linked_at: datetime (nullable)
created_at: datetime
```

## Auth Flow (WebAuthn Passkey)

1. User navigates to /signup, enters display name
2. Frontend prompts for passkey creation (Face ID, Touch ID, PIN, security key, etc.)
3. Backend stores credential in database (user + credential tables)
4. Backend issues HS256 JWT session token (HttpOnly cookie)
5. User redirected to /notes (protected route)

**Login Flow:**
1. User navigates to /login
2. Frontend prompts for passkey authentication
3. Backend verifies challenge response
4. Backend issues HS256 JWT session token
5. User redirected to /notes

**API Requests:**
1. Frontend includes Authorization: Bearer token (or uses HttpOnly cookie)
2. Backend validates HS256 JWT signature using JWT_SECRET
3. Extracts user_id from `sub` claim
4. All database queries filtered by user_id
5. Logout clears the session cookie

## Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/notesapp
JWT_SECRET=change-me-in-production-use-64-char-random-string
JWT_EXPIRY_DAYS=7
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=NotesApp
WEBAUTHN_ORIGIN=http://localhost:3000
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=notesapp-images
MINIO_MAX_IMAGE_SIZE=10485760
TELEGRAM_BOT_TOKEN=xxx (optional)
CORS_ORIGINS=http://localhost:3000,https://example.com
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Database Setup

Uses Alembic for migrations. Initial migration creates all tables.

```bash
cd backend
alembic upgrade head     # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration
alembic downgrade -1     # Rollback one migration
```

## Deployment

See [`docs/deployment-guide.md`](./docs/deployment-guide.md) for production setup.

## Documentation

- [`docs/project-overview-pdr.md`](./docs/project-overview-pdr.md) - Product requirements & vision
- [`docs/codebase-summary.md`](./docs/codebase-summary.md) - File structure & module descriptions
- [`docs/code-standards.md`](./docs/code-standards.md) - Coding conventions & patterns
- [`docs/system-architecture.md`](./docs/system-architecture.md) - Architecture diagrams & data flow
- [`docs/project-roadmap.md`](./docs/project-roadmap.md) - Features & milestones
- [`docs/deployment-guide.md`](./docs/deployment-guide.md) - Local & production deployment
- [`docs/design-guidelines.md`](./docs/design-guidelines.md) - UI patterns & component design

## Support

For issues or questions, open a GitHub issue or contact the team.
