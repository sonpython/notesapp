# NotesApp

A modern, full-stack note-taking and todo management application with Telegram reminder integration.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.13 (via `uv`)
- Node.js 22+
- pnpm 10.29.3+

### Local Development

```bash
# Install dependencies
pnpm install

# Set up environment
cp backend/.env.example backend/.env
cp apps/web/.env.example apps/web/.env.local

# Start database & backend
docker-compose up -d

# Run database migrations (first time only)
cd backend && alembic upgrade head && cd ..

# Start dev servers
pnpm dev
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432

### Development Commands

```bash
pnpm dev              # Run all services in dev mode
pnpm build            # Build frontend and backend
pnpm lint             # Lint all packages
pnpm dev:web          # Frontend only
pnpm build:web        # Build frontend only
pnpm lint:web         # Lint frontend only
```

## Architecture Overview

### Stack
- **Backend**: FastAPI + SQLAlchemy async + asyncpg + Alembic (Python 3.13)
- **Frontend**: Next.js 16 (App Router) + React 19 + TailwindCSS v4
- **Database**: PostgreSQL (local or Supabase as data backend)
- **Auth**: Passkey-only (WebAuthn/FIDO2) with local HS256 JWT sessions
- **Infrastructure**: pnpm monorepo + Turborepo, Docker Compose

### Key Features
- **Notes**: Rich text editing (CodeMirror), auto-save with debounce, pinned/archived states, folder organization
- **Todos**: Hierarchical todos with subtasks, priority levels, deadlines, reminder scheduling
- **Folders**: Nested folder hierarchy for note organization
- **Telegram**: Direct reminder delivery via Telegram bot, per-user link code pairing
- **Auth**: Session-based auth with automatic token refresh, role-based access control

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, scheduler
│   │   ├── config.py            # Settings from .env
│   │   ├── database.py          # SQLAlchemy async engine & session
│   │   ├── deps.py              # JWT auth dependency
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   └── tasks/               # Background jobs (APScheduler)
│   ├── alembic/                 # Database migrations
│   ├── Dockerfile               # Backend container
│   └── pyproject.toml           # Python dependencies (uv)
├── apps/web/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utilities (API client, Supabase, types)
│   │   ├── middleware.ts        # Session refresh, route protection
│   │   └── globals.css          # TailwindCSS v4 styles
│   ├── package.json             # Node dependencies
│   └── next.config.ts           # Next.js config
├── docker-compose.yml           # Local dev environment
├── pnpm-workspace.yaml          # Monorepo config
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
note_id: UUID (FK to notes, nullable)
priority: int (0=none, 1=low, 2=medium, 3=high)
sort_order: int
reminder_at: datetime (nullable)
reminder_sent: boolean
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

## Auth Flow

1. User registers with display name, creates passkey (Face ID/Touch ID/PIN)
2. Backend creates user + credential, issues HS256 JWT as HttpOnly cookie
3. Login: user authenticates with passkey, backend validates and issues JWT cookie
4. Frontend calls API with `credentials: 'include'`, cookie sent automatically
5. Backend validates JWT from cookie (or Bearer header for API clients)
6. All database queries filtered by `user_id` from JWT `sub` claim
7. Logout clears the session cookie

## Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/notesapp
JWT_SECRET=change-me-in-production-use-64-char-random-string
JWT_EXPIRY_DAYS=7
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=NotesApp
WEBAUTHN_ORIGIN=http://localhost:3000
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
