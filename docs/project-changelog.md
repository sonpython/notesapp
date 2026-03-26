# Project Changelog

All notable changes to NotesApp are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Planned
- Email/push notifications for reminders
- Note sharing with permissions
- Real-time collaborative editing
- Note templates
- Quick capture widget
- Slack/Discord/WhatsApp integrations
- Mobile apps (React Native, native iOS/Android)
- Web clipper browser extension
- Analytics dashboard

---

## [0.7.0] - 2026-03-26

### Added: Todo Folders, MCP Server, UI Improvements

#### Todo Folder Organization (NEW)
- **Separate todo_folders table** - distinct from note folders
- **Nested hierarchy** - parent_id self-referential for folder nesting
- **Default folder** - "Personal" folder auto-created per user (via migration)
- **Backend API**: `/api/todo-folders/` with CRUD + stats endpoint
  - GET / (paginated list)
  - POST / (create)
  - PUT /{id} (update)
  - DELETE /{id} (delete)
  - GET /{id}/stats (completion percentage)
- **Todo model update**: folder_id FK (nullable, SET NULL on delete)
- **IndexedDB offline**: todo folder sync support

#### MCP Server Integration (NEW)
- **FastMCP Python server** - `backend/mcp_server.py` (161 LOC)
- **10 tools for AI agents**:
  - list_todo_folders(), create_todo_folder(), update_todo_folder(), delete_todo_folder()
  - list_todos(), create_todo(), update_todo(), delete_todo(), toggle_todo()
  - get_folder_stats()
- **Environment variables**: NOTESAPP_USER_ID, DATABASE_URL
- **Transport**: stdio (Claude Desktop native)
- **Claude Desktop config**: JSON configuration in ~/.claude/config.json
- **New service**: mcp_todo_service.py (186 LOC) with tool implementations

#### Frontend UI Enhancements
- **Sidebar Accordion** - Notes and Todos as collapsible sections
  - Only one section expanded at a time
  - Each section has independent folder tree
  - Auto-expands based on current route (/notes or /todos)
- **Completion % Badges** - parent todos show completion percentage
  - Format: "X% completed" as muted text after title
  - Calculated from direct children only
  - Formula: Math.round((completed / total) * 100)
- **TodoFolderTree component** (112 LOC) - tree rendering with context menu
- **TodoFolderTreeItem component** (164 LOC) - individual folder UI
- **TodoFoldersStore** (163 LOC) - Svelte store for CRUD + caching

#### New Files Created
Backend:
- `backend/app/models/todo_folder.py` (78 LOC)
- `backend/app/schemas/todo_folder.py` (35 LOC)
- `backend/app/routers/todo_folders.py` (139 LOC)
- `backend/app/services/mcp_todo_service.py` (186 LOC)
- `backend/mcp_server.py` (161 LOC)
- `backend/alembic/versions/20260325_..._add_todo_folders.py`

Frontend:
- `apps/web-svelte/src/lib/stores/todo-folders-store.svelte.ts` (163 LOC)
- `apps/web-svelte/src/lib/offline/indexed-db-todo-folders.ts` (32 LOC)
- `apps/web-svelte/src/lib/components/todo-folders/todo-folder-tree.svelte` (112 LOC)
- `apps/web-svelte/src/lib/components/todo-folders/todo-folder-tree-item.svelte` (164 LOC)

#### UI/UX Improvements
- Keyboard shortcuts: Ctrl+S/Cmd+S intercepted to save note (not browser save)
- Note editor cursor no longer jumps during autosave
- Title auto-generation deferred to note leave event
- Todo drag-and-drop only active in reorder mode
- Reminders skip completed todos
- Shared note markdown rendering fixed (typography + marked GFM)
- WYSIWYG editor typography improvements
- Multi-account Telegram support

#### Infrastructure
- CD switched to self-hosted GitHub Actions runner
- Frontend healthcheck uses bun instead of curl
- Docker healthchecks for all services

### Documentation Updated
- README.md: MCP section, todo folders, updated API endpoints
- system-architecture.md: MCP architecture diagram, todo folders data model, new schema
- codebase-summary.md: New files, updated LOC counts, MCP section
- code-standards.md: MCP tool naming conventions
- deployment-guide.md: MCP server setup for Claude Desktop
- project-roadmap.md: Phase 4 progress (75%), todo folders completed

### Technical Details
- **Files Added**: 11 new files (backend + frontend + migrations)
- **LOC Added**: ~1,500 lines (backend + frontend)
- **Database**: New table (todo_folders), migration includes default folder creation
- **API Endpoints**: 5 new endpoints for todo folder management
- **Store Updates**: All offline stores updated for todo folder sync

### Migration
```bash
alembic upgrade head  # Auto-creates todo_folders table and "Personal" folder for users
```

---

## [0.7.1] - 2026-03-26

### Added: MCP HTTP Transport & Cascade Delete

#### MCP HTTP Transport (Breaking: stdio → HTTP)
- **FastMCP HTTP transport** - Streamable-HTTP at `/api/mcp`
- **Pure ASGI McpAuthMiddleware** - avoids SQLAlchemy greenlet async context issues
  - Supports `?api_key=xxx` query parameter
  - Supports `Authorization: Bearer <key>` header
  - SHA256 hash validation via api_keys table
- **ApiKey Model** (NEW) - id, user_id, name, key_hash, key_prefix, expires_at, last_used_at
- **Claude Code config** - HTTP URL instead of stdio command
- **Stateless architecture** - no process-based user context

#### Cascade Delete (Optional)
- **Query parameter support**: `DELETE /api/folders/{id}?cascade=true`
- **Default behavior unchanged**: items SET NULL on folder_id (preserved)
- **Cascade option**: delete all items in folder when cascading
- **Frontend modal**: confirmation dialog with "Also delete items" checkbox
- **Applies to**: notes folders, todo folders (both support cascade)

#### New Files
Backend:
- `backend/app/models/api_key.py` (68 LOC)
- `backend/app/middleware/mcp_auth.py` (150 LOC)
- `backend/app/routers/mcp_router.py` (80 LOC)

#### Dependencies
- Added: fastmcp[sse] for HTTP transport support
- Removed: stdoutLogger dependency (not needed for HTTP)

#### Documentation Updated
- system-architecture.md: MCP HTTP architecture, ApiKey table schema, Claude Code config
- code-standards.md: ASGI middleware pattern, cascade delete patterns, MCP HTTP conventions
- deployment-guide.md: MCP HTTP setup with API key generation

### Technical Details
- **Breaking Change**: MCP transport switched from stdio to HTTP
  - Claude Desktop users must update config to use HTTP URL
  - API key must be generated and stored in api_keys table
  - Old stdio-based configs will no longer work
- **Performance**: HTTP transport enables stateless scaling (no process-per-user)
- **Security**: API key hash stored in DB, not in plain text

---

## [0.6.2] - 2026-02-22

### Infrastructure: CI/CD with Cloudflare Tunnel

#### Deployment Pipeline
- **Cloudflare Tunnel SSH**: Replaced direct SSH with cloudflared ProxyCommand
- **Deploy Keys**: Server uses GitHub deploy key for secure repo access
- **Zero Trust**: No exposed ports, all traffic through Cloudflare Tunnel

#### CI/CD Workflow
- **CI**: Lint (ruff), tests (pytest), build (bun) on push/PR
- **CD**: Auto-deploy on CI success via SSH through Cloudflare Tunnel
- **Migration**: Auto-run alembic migrations after deploy

#### Security
- SSH key-only auth (password disabled)
- Deploy key scoped to single repo (read-only)
- No static IP or open ports required

---

## [0.6.1] - 2026-02-21

### Fixed: API URL Handling & Image Upload Tests

#### API URL Improvements
- **Trailing Slash Convention**: All API endpoints now use trailing slashes (`/api/auth/register/`, `/api/notes/`, `/api/images/upload/`)
  - Prevents FastAPI 307 redirect responses
  - Standardized across all routers (auth, notes, images, todos, folders, telegram)
  - Frontend API client updated to use trailing slashes
- **Frontend API Changes**: Updated `api.ts` to include trailing slashes in all fetch calls
- **Relative URLs**: Configured frontend to use relative API paths, preventing mixed content in Docker
- **Vite HMR Configuration**: Added HMR settings for Docker development environment

#### Image Upload Testing (15 new tests)
- **Test Coverage**: Parameterized tests for all 8 supported MIME types
  - `image/png`, `image/jpeg`, `image/gif`, `image/webp`, `image/svg+xml`, `image/heic`, `image/heif`, `image/tiff`
- **Test Categories**:
  - Individual format tests (PNG, JPEG, HEIC, TIFF)
  - Allowed content type validation (8 formats)
  - Invalid content type rejection (text/plain, application/octet-stream)
  - Authentication requirement verification
  - File size limit validation
- **Test File**: `backend/tests/test_images_router.py` (168 LOC)
- **Backend Tests**: Total now 37+ tests (22 → 37)

#### Image Format Support
- **Added MIME Types**: `image/heic`, `image/heif`, `image/tiff` to allowed uploads
- **MinIO Service**: Updated `ALLOWED_CONTENT_TYPES` and `CONTENT_TYPE_TO_EXT` mappings
- **Support Summary**: 8 formats (png, jpeg, gif, webp, svg, heic, heif, tiff)

#### Frontend UI Enhancements
- **Image Icon Indicator**: Added image icon badge to note list items containing images
- **Real-time Updates**: Fixed note count updates in sidebar via custom events
- **Service Worker**: Updated cache versioning for proper invalidation on updates

### Technical Details
- **API Compliance**: FastAPI route decorators now include trailing slashes
- **Content-Type Header**: Explicit content-type in multipart form uploads
- **Test Architecture**: Mock-based testing with AsyncMock for MinIO service
- **Files Modified**: 9 files (api.ts, note-list.svelte, stores, service-worker, config, minio_storage_service, vite.config.ts, test_images_router.py)
- **Tests Added**: 15 parameterized image upload tests

---

## [0.6.0] - 2026-02-19

### Added: Image Upload with MinIO (AZD-63)

#### Backend Image Storage
- **MinIO Integration**: S3-compatible object storage (local or cloud)
- **New Service**: minio_storage_service.py (157 LOC)
- **New Router**: images.py (136 LOC) with endpoints:
  - POST /api/images/upload (multipart form, 10MB max)
  - GET /api/images/{id} (serve image with backend proxy auth)
  - DELETE /api/images/{id} (delete image)
  - GET /api/images (list user images)
- **Storage Structure**: users/{user_id}/images/{uuid}.{ext}
- **Allowed Types**: jpeg, png, gif, webp, svg+xml
- **Auth**: All image endpoints require Bearer JWT
- **Caching**: 1-day HTTP cache on GET image requests

#### Frontend Image Handling
- **New Service**: image-upload-service.ts (validation, upload)
- **New Extension**: codemirror-image-drop-extension.ts (139 LOC)
  - Drag-and-drop image insertion
  - Paste image from clipboard
  - Upload progress indicator
  - Error handling & user feedback
- **Integration**: Note editor supports image upload seamlessly
- **UI Feedback**: Upload progress, error messages, success confirmation

#### Configuration
- New .env vars: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_MAX_IMAGE_SIZE
- Docker Compose: MinIO service (ports 9000/9001) for local development
- MinIO Console: localhost:9001 for bucket management

#### Docker Updates
- MinIO service added to docker-compose.yml
- Bucket initialization on startup
- Health checks for MinIO service

### Technical Details
- **Backend Files**: minio_storage_service.py, images.py, image.py schema
- **Frontend Files**: image-upload-service.ts, codemirror-image-drop-extension.ts
- **LOC**: ~433 lines added (backend + frontend)
- **Dependencies**: miniopy-async for async MinIO operations

### Documentation Updated
- README: Added image upload to Stack, Features, API Endpoints, Config
- system-architecture.md: MinIO in data tier, Images API section, upload flow diagram
- codebase-summary.md: New image services and routers documented
- deployment-guide.md: MinIO service details, env vars

---

## [0.5.0] - 2026-02-18

### Added: SvelteKit Frontend Migration (Phases 1-3 Complete)

#### Frontend Framework Migration
- **SvelteKit 2 + Svelte 5 primary frontend** (in progress)
  - New apps/web-svelte/ directory with full feature parity to Next.js
  - Rune-based reactive stores (svelte.ts files)
  - Server-side hooks (hooks.server.ts)
  - TailwindCSS v4 integration
  - Vitest setup for component/store testing

#### Authentication: Passkey WebAuthn
- **Migration from Supabase to local passkey auth**
  - WebAuthn/FIDO2 registration and authentication
  - Passkey credential storage in database
  - HS256 JWT session tokens (local JWT_SECRET)
  - No third-party auth dependency
  - HttpOnly cookie + localStorage fallback
  - User model + credential model (SQLAlchemy)
  - WebAuthn registration API: POST /api/auth/register
  - WebAuthn authentication API: POST /api/auth/authenticate
  - Updated deps.py for HS256 validation (removed Supabase JWKS)

#### Backend Changes
- **Auth Models**: User & Credential tables for local auth
- **Auth Schemas**: PasskeyRegistration, PasskeyAuthentication schemas
- **JWT Auth**: HS256 only, passkey-backed user sessions
- **Note Export Service**: Lazy import of WeasyPrint (reduce startup time)
- **Removed**: Duplicate Alembic migration files (consolidated to single 20260213 migration)

#### Frontend Structure - SvelteKit
- **Stores**: auth, notes, todos, folders, tags, online-status (all Svelte stores)
- **Routes**: Landing, login, signup, notes, todos, settings, offline (same as Next.js)
- **Offline Support**: IndexedDB + sync engine (ported from Next.js)
- **UI Components**: Same feature set as Next.js (notes editor, todos, folders, tags)
- **Styling**: TailwindCSS v4, dark/light/system theme toggle

#### Next.js App (Deprecated)
- **Status**: Legacy app kept for reference during migration
- **Path**: apps/web/ (will be removed in v1.0)
- **Note**: Outdated Supabase auth, kept for comparison only

### Changed
- Backend auth system (Supabase → local HS256 passkey)
- Frontend primary (Next.js → SvelteKit)
- Database schema (added user & credential tables)
- JWT validation (ES256 JWKS → HS256 HS256_secret)

### Technical Details
- **Files Added**: ~28 SvelteKit routes/components, auth models & schemas, webauthn services
- **Files Removed**: Duplicate Alembic migration
- **Database Tables**: 2 new (user, credential)
- **API Changes**: POST /auth/register, POST /auth/authenticate, removed Supabase dependencies
- **Dependencies**: Added webauthn, @simplewebauthn/browser, removed @supabase packages
- **Code**: ~2,500 LOC added (SvelteKit), ~500 LOC removed (deprecated code)

### Testing
- SvelteKit routes functional (pages load correctly)
- WebAuthn registration and login flows tested
- API JWT validation updated for HS256
- Offline support ported and functional
- PWA service worker functional with new auth

### Migration Path
- Phases 1-3 complete: Core features, auth, offline support
- Phase 4 in progress: Advanced features, full test coverage
- v1.0: Next.js app removed, SvelteKit as primary frontend

---

## [0.4.0] - 2026-02-15

### Added: Phase 4 Advanced Features (60% complete)

#### Performance Optimization (AZD-13)
- Database indexes on search fields (tags, reminders, folder relationships)
- API pagination support (limit/offset) on list endpoints
- API rate limiting via slowapi (50 req/min per user)
- Response time monitoring baseline (~50-100ms local, ~150-200ms network)

#### Theme Toggle (AZD-16)
- Dark/light/system theme support
- User theme preference persistence
- Dynamic CSS variables for theming
- Theme context provider for global theme state
- Toggle UI in app header and settings page
- TailwindCSS v4 theme integration

#### Note Export (AZD-17)
- Export single notes or note collections as:
  - **Markdown**: Formatted text with metadata
  - **PDF**: Styled PDF with folder hierarchy
  - **ZIP**: Batch export with folder structure
- Export menu integrated in notes list UI
- Metadata export (title, created_at, tags, folder)
- Preserves formatting and relationships

#### Recurring Todos (AZD-18)
- Recurrence types: daily, weekly, monthly
- Interval multiplier (e.g., "every 2 weeks")
- Weekly recurrence: select specific weekdays
- Monthly recurrence: day-of-month selection
- Recurrence end date (optional, null = forever)
- Automatic todo instance generation
- Recurrence parent tracking for lineage
- UI: Recurrence selector in todo create/edit forms

#### Tags/Labels System (AZD-19)
- Create, read, update, delete tags per user
- Tag colors for visual organization
- Many-to-many relationships: notes ↔ tags, todos ↔ tags
- Tag filtering on notes and todos lists
- Tag badge UI components
- Bulk tag assignment to multiple items
- Tag autocomplete in search/filter

#### PWA & Offline Support (AZD-20)
- Service worker for static asset caching
- IndexedDB storage for offline notes, todos, folders
- Offline sync queue for pending changes
- Sync engine: retry failed ops when reconnected
- Offline indicator UI (shows sync status)
- Works offline: view, create, edit items (locally)
- Auto-sync when online restored
- PWA install prompt for home screen
- Fallback offline page (~offline route)

#### Testing Infrastructure
- Backend: pytest with 22+ unit tests
- Backend test coverage: authentication, CRUD operations, export
- Frontend: vitest setup with test files for hooks, components
- GitHub Actions CI/CD pipeline
- Automated linting (ESLint, black)
- Type checking (TypeScript, mypy)

### Changed
- Extended todos model with recurrence fields
- Added tags table with junction tables (note_tags, todo_tags)
- Updated API responses to include tag information
- Frontend hooks refactored to support tags and recurrence
- Theme system replaces hardcoded dark-only mode
- Database indexes optimized for tag and reminder queries

### Technical Details
- **Files Added**: ~15 new components, 8 new services, 5 new hooks, offline modules
- **Database Tables**: 3 new (tags, note_tags, todo_tags)
- **API Endpoints**: +8 new endpoints (tags, export, pagination params)
- **Dependencies**: python-pptx for PDF export, zlib for ZIP compression
- **Code**: ~1,500 LOC added (backend + frontend)

---

## [0.3.0] - 2026-01-31

### Added: Phase 3 Testing & Quality

#### CI/CD Pipeline
- GitHub Actions workflow for automated testing
- Automated linting and type checking
- Pre-commit hooks for code quality
- Build validation on pull requests

#### Backend Test Infrastructure
- pytest setup with fixtures and test utilities
- 22+ unit tests covering:
  - Authentication (JWT validation, user context)
  - CRUD operations (notes, todos, folders)
  - Query filtering (search, pagination, status)
  - Error handling (404, 400, 401)
- Mock Telegram API responses
- Database fixtures for test isolation

#### Frontend Test Infrastructure
- vitest setup with React Testing Library
- Component snapshot tests
- Hook tests with custom test utilities
- API client mocking

#### Documentation
- Enhanced OpenAPI documentation
- API endpoint descriptions
- Request/response schemas documented
- Error response patterns documented

---

## [0.2.0] - 2026-01-14

### Added: Phase 2 Enhancements

#### Telegram Integration
- Telegram bot API integration
- Per-user link code for account linking
- Store chat_id & settings in database
- Webhook endpoint for bot messages
- Telegram commands:
  - `/start <link_code>` - Link Telegram account
  - `/todo <title>` - Create todo from Telegram
  - `/list` - Show active todos
  - `/done <n>` - Mark todo complete

#### Reminders
- Deadline field on todos
- reminder_at field for scheduled reminders
- reminder_sent boolean flag
- APScheduler background task (60s interval)
- Check pending reminders and send via Telegram
- Mark reminders as sent to avoid duplicates

#### Frontend Features
- Auto-save notes (500ms debounce)
- Optimistic note updates (instant UI feedback)
- Filter todos by completion status (active/completed)
- Filter todos by priority (none/low/medium/high)
- Filter notes by folder and archive status
- Full-text search on notes (PostgreSQL tsvector/tsquery)

#### API Enhancements
- Proper error responses (4xx, 5xx with detail messages)
- Status codes: 200, 201, 400, 404, 500
- Query filtering standardized across endpoints
- API rate limiting infrastructure ready

---

## [0.1.0] - 2026-01-01

### Added: Phase 1 Core Features

#### Notes Management
- Create, edit, delete notes
- Note titles and rich content
- Auto-save with debounce (500ms)
- Pin/unpin important notes
- Archive/restore notes
- CodeMirror editor for syntax highlighting
- Markdown preview
- CRUD API endpoints

#### Todos Management
- Create, edit, delete todos
- Subtodos (hierarchical support)
- Toggle completion status with completion_at timestamp
- Priority levels (0=none, 1=low, 2=medium, 3=high)
- Deadlines for todos
- Recursive rendering for nested todos
- CRUD API endpoints

#### Folders
- Create nested folders
- Rename and delete folders
- Move notes to folders
- Cascading delete (folder → notes)
- Folder tree visualization with expand/collapse
- Drag-drop notes to folders
- Self-referential parent_id relationships

#### Authentication
- Supabase email/password signup
- Supabase email/password login
- Session management with auto-refresh
- Protected routes via middleware
- JWT validation (ES256 via JWKS + HS256 fallback)
- User context isolation (all queries filtered by user_id)

#### Database
- PostgreSQL schema (4 tables: notes, todos, folders, telegram_settings)
- Alembic migrations for version control
- User isolation via user_id filtering
- Proper indexing for performance
- Foreign key relationships with cascading deletes
- Timestamps (created_at, updated_at) on all tables

#### Frontend UI
- Landing page (public)
- Login/signup pages
- Notes page (2-column: list + editor)
- Todos page (list with priority/status)
- Settings page (profile + Telegram)
- Sidebar (navigation, folders, user menu)
- Header (mobile hamburger menu)
- Dark theme default
- Responsive design (desktop + mobile)
- TailwindCSS v4 styling

#### Backend Stack
- FastAPI web framework
- SQLAlchemy async ORM
- asyncpg for async database access
- Pydantic for validation
- CORS middleware
- Request logging

#### Frontend Stack
- Next.js 16 (App Router)
- React 19
- TailwindCSS v4
- Supabase Auth (@supabase/ssr)
- CodeMirror for editing
- React Markdown for preview
- Lucide React icons

---

## Versioning Scheme

- **Major**: Phase completion (0→1 for Phase 1 complete, etc.)
- **Minor**: Feature additions (API updates, UI improvements)
- **Patch**: Bug fixes and documentation updates

## Release Timeline

| Version | Date | Milestone |
|---------|------|-----------|
| 0.1.0 | 2026-01-01 | Phase 1: Core Features Complete |
| 0.2.0 | 2026-01-14 | Phase 2: Telegram + Reminders |
| 0.3.0 | 2026-01-31 | Phase 3: Testing & CI/CD |
| 0.4.0 | 2026-02-15 | Phase 4: Advanced Features (60%) |
| 0.5.0 | 2026-02-18 | SvelteKit Migration (Phases 1-3 complete, passkey auth) |
| 0.6.0 | 2026-02-19 | Image Upload with MinIO (AZD-63) |
| 1.0.0 | TBD | Production Ready (SvelteKit primary, Phase 4 100%) |

## Breaking Changes

### v0.2.0 → v0.3.0
- None (backward compatible)

### v0.1.0 → v0.2.0
- None (backward compatible)

## Migration Guides

All versions use Alembic migrations for database changes. Run:
```bash
alembic upgrade head
```

---

## Contributors

- Michael Phan - Full-stack developer

## License

MIT (see LICENSE file)

## Support

- GitHub Issues: Report bugs and request features
- Documentation: See `/docs` directory
- Roadmap: See `project-roadmap.md`
