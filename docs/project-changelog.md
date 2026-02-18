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
- Phase 4 completion (final features)

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
