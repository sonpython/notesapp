# Project Overview & Product Development Requirements

## Vision

NotesApp is a lightweight, modern note-taking and task management platform with seamless Telegram integration. It combines the simplicity of note-taking with advanced todo management, enabling users to organize thoughts, manage tasks, and receive reminders via their preferred messaging platform.

## Project Goals

- **Simplicity**: Intuitive UI for rapid note capture and task management
- **Reliability**: Real-time sync, automatic saving, persistent state
- **Integration**: Telegram reminders for timely task notifications
- **Performance**: Instant UI feedback, minimal latency, optimized queries
- **Scalability**: Async-first architecture supporting concurrent users

## Target Users

- Knowledge workers managing notes and tasks
- Teams coordinating via Telegram
- Individuals wanting centralized task tracking with messaging integration

## Core Features

### 1. Notes Management
- Create, edit, delete, and archive notes
- Rich text editing with CodeMirror
- Auto-save with 500ms debounce
- Pin important notes to top of list
- Organize notes into folders (nested hierarchy)
- Full-text search & filtering by folder/archive status
- Image uploads via drag-drop or paste (up to 10MB per image)
- Timestamps (created_at, updated_at)

### 2. Todo Management
- Create, update, complete, and delete todos
- Hierarchical subtasks (parent-child relationships)
- Priority levels: None (0), Low (1), Medium (2), High (3)
- Deadlines with optional reminders
- Auto-scheduled reminder sending via APScheduler
- Inline editing & bulk operations
- Sort by priority, deadline, or custom order
- Toggle completion status with single click
- Optional link to parent note

### 3. Folder Organization
- Create nested folders for note organization
- Auto-delete empty folders (via cascading FK)
- Icon support for visual identification
- Drag-and-drop reorganization (future)
- Share folders with users (future)

### 4. Telegram Integration
- Per-user link code for Telegram bot pairing
- Automatic reminder delivery via Telegram
- Enable/disable reminders without unlinking
- One-way notifications (no commands in bot)
- Support for multiple reminders per todo

### 5. Authentication & Authorization
- Email/password signup & login (Supabase Auth)
- Session-based security with automatic refresh
- JWT validation (ES256 JWKS + HS256 fallback)
- User isolation: all data filtered by user_id
- Secure token storage in httpOnly cookies

## Non-Functional Requirements

### Performance
- API response time: < 200ms (p95)
- Page load: < 2s (3G network)
- Note auto-save latency: < 1s (after debounce)
- Database query optimization: indexed user_id queries
- Connection pooling: Supabase session mode pooler

### Reliability
- 99.5% uptime target (development phase)
- Graceful degradation: UI functional offline (local state)
- Automatic error recovery & retry logic
- Optimistic UI updates with rollback on failure
- Database transaction integrity (ACID)

### Security
- HTTPS/TLS in production
- SQL injection prevention via SQLAlchemy ORM
- CSRF protection via SameSite cookies
- XSS prevention via React/Next.js auto-escaping
- Rate limiting on Telegram webhook (future)
- Input validation (Pydantic schemas)

### Scalability
- Stateless backend (FastAPI)
- Async-first (asyncio + asyncpg)
- Connection pooling (pool_pre_ping=True)
- Horizontal scaling: add FastAPI instances + load balancer
- Database: Supabase managed PostgreSQL

### Maintainability
- Clear folder structure & module organization
- DRY principle: shared schemas, reusable hooks
- Type hints (Python, TypeScript)
- Minimal dependencies (FastAPI, SQLAlchemy, Next.js)
- Self-documenting code with comments on complex logic

## Acceptance Criteria

### Notes Feature
- [x] Create note with title & content
- [x] Edit note title & content with auto-save
- [x] Delete note with confirmation
- [x] Pin/unpin note
- [x] Archive/restore note
- [x] Move note to folder
- [x] Filter by folder, archive, pinned status
- [x] Sort by created_at, updated_at
- [x] Full-text search (PostgreSQL tsvector)
- [x] Image uploads via drag-drop/paste (up to 10MB)
- [ ] Collaborative editing (future)

### Todos Feature
- [x] Create todo with title, description, deadline
- [x] Create subtodos (nested)
- [x] Edit todo details inline
- [x] Toggle completion status
- [x] Delete todo & children
- [x] Set priority level
- [x] Set reminder time
- [x] Filter by completion, priority, deadline
- [x] Auto-send reminders via Telegram
- [ ] Bulk operations (select multiple)
- [ ] Drag-drop reordering (future)

### Folders Feature
- [x] Create folder with optional parent
- [x] Rename folder
- [x] Delete folder (cascade to notes)
- [x] List folders with nesting
- [ ] Folder sharing (future)
- [ ] Folder permissions (future)

### Telegram Integration
- [x] Generate link code for bot pairing
- [x] Link Telegram account to user
- [x] Unlink Telegram account
- [x] Send reminders via Telegram
- [x] Display link status in settings
- [ ] Telegram commands for todo creation (future)
- [ ] Rich message formatting (future)

### Auth & UX
- [x] Sign up with email/password
- [x] Login with email/password
- [x] Logout
- [x] Auto-refresh session tokens
- [x] Redirect unauthenticated users to login
- [ ] Forgot password flow (planned)
- [ ] Email verification (planned)
- [ ] Social login (future)

## Known Limitations & Gaps

### Missing Features
- No automated test suite (test infrastructure in progress)
- No CI/CD pipeline (manual deployment required)
- No full-text search on notes (indexed filtering only)
- No collaborative/real-time editing
- Folders UI stubbed (API implemented, frontend basic)
- No user profile customization
- No dark/light theme toggle (dark theme default only)
- No offline-first PWA support

### Scalability Constraints
- Single database instance (no replication)
- No caching layer (Redis)
- No CDN for static assets
- APScheduler runs in single process (no distributed scheduling)
- Max concurrent WebSocket connections limited by instance

### Security Gaps (Future)
- No rate limiting on API endpoints
- No audit logging of data modifications
- No encryption at rest
- No 2FA support
- No API key authentication (user-only auth)

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Page Load Time (p95) | < 2s | TBD |
| API Response (p95) | < 200ms | TBD |
| Note Save Latency | < 1s | < 500ms (debounced) |
| Uptime | 99.5% | TBD |
| Test Coverage | > 80% | 0% |
| User Adoption | 100 active users | 1-5 (beta) |

## Timeline & Milestones

### Phase 1: Core (Complete)
- Notes CRUD + folders
- Todos CRUD + hierarchy
- Supabase auth
- API & database schema

### Phase 2: Enhancement (In Progress)
- Telegram integration
- Auto-reminders
- Improved UI/UX
- Settings page

### Phase 3: Polish & Testing (Planned)
- Automated test suite
- CI/CD pipeline
- Performance optimization
- Security audit

### Phase 4: Advanced Features (Future)
- Full-text search
- Collaborative editing
- Mobile app (React Native)
- API for third-party integrations

## Dependencies & Constraints

### External Dependencies
- Supabase (auth + database)
- Telegram Bot API
- AWS/GCP for backend hosting (future)

### Technical Constraints
- Python 3.13+ required
- Node.js 22+ required
- PostgreSQL 15+ required
- Bun 1.2.4+ package manager (no npm/pnpm/yarn)

### Organizational Constraints
- Single developer (current)
- Limited DevOps resources
- Manual deployment process
- No production monitoring yet

## Cost Considerations

- Supabase: free tier (2 GB DB, 50k MAU)
- Telegram: free (API)
- Infrastructure: $10-50/month (VPS or managed platform)
- Development: volunteer (no budget allocated)

## Future Roadmap

- [ ] Mobile app (React Native or Flutter)
- [ ] Collaborative workspaces
- [ ] Advanced scheduling & recurring reminders
- [ ] Integration with Slack, Discord, WhatsApp
- [ ] Note templates & quick capture
- [ ] Time tracking for todos
- [ ] Analytics dashboard
- [ ] AI-powered tagging & summarization

## References

- Architecture: [`docs/system-architecture.md`](./system-architecture.md)
- Code Standards: [`docs/code-standards.md`](./code-standards.md)
- Deployment: [`docs/deployment-guide.md`](./deployment-guide.md)
