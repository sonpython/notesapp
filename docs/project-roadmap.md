# Project Roadmap

## Current Status

**Phase**: Core + Enhancements + Advanced (3/4 started, Phase 4: 60% complete)
**Last Updated**: 2026-02-15
**Overall Progress**: ~85%

## Phase 1: Core Features (100% Complete)

### Notes Management
- [x] Create notes with title & content
- [x] Edit notes with auto-save (500ms debounce)
- [x] Delete notes
- [x] Pin/unpin important notes
- [x] Archive/restore notes
- [x] Rich text editing (CodeMirror)
- [x] API endpoints (CRUD)
- [x] Database schema & migrations

### Folders
- [x] Create nested folders
- [x] Rename/delete folders
- [x] Move notes to folders
- [x] API endpoints (CRUD)
- [x] Cascading delete (folder → notes)
- [x] Database schema
- [x] Frontend UI (folder tree with CRUD context menu)
- [x] Folder tree visualization (expand/collapse)
- [x] Drag-drop notes to folders

### Todos
- [x] Create todos with title, description, deadline
- [x] Create subtodos (hierarchical)
- [x] Edit todos inline
- [x] Toggle completion status
- [x] Delete todos & children
- [x] Set priority (0=none, 1=low, 2=medium, 3=high)
- [x] API endpoints (CRUD + toggle)
- [x] Database schema
- [x] Recursive rendering (nested display)

### Auth
- [x] Supabase email/password signup
- [x] Supabase email/password login
- [x] Session management with auto-refresh
- [x] Protected routes (middleware)
- [x] JWT validation (ES256 JWKS + HS256)
- [x] User context in all queries

### Database
- [x] PostgreSQL schema (4 tables)
- [x] Alembic migrations
- [x] User isolation (user_id filtering)
- [x] Proper indexing (user_id, FK)
- [x] Timestamps (created_at, updated_at)

### Frontend UI
- [x] Landing page
- [x] Login/signup pages
- [x] Notes page (2-column: list + editor)
- [x] Todos page (list with filters)
- [x] Settings page (profile + telegram)
- [x] Sidebar (navigation, folders, user menu)
- [x] Header (mobile hamburger)
- [x] Dark theme default
- [x] Responsive design (desktop + mobile)

## Phase 2: Enhancement (100% Complete)

### Telegram Integration
- [x] Telegram bot API integration
- [x] Per-user link code generation
- [x] Link Telegram account to user
- [x] Unlink Telegram account
- [x] Store chat_id & settings in database
- [x] Webhook endpoint for bot messages
- [x] Telegram service layer
- [x] Settings page UI
- [x] Telegram commands (/todo, /list, /done)

### Reminders
- [x] Deadline field on todos
- [x] reminder_at field on todos
- [x] reminder_sent boolean flag
- [x] APScheduler background task (every 60s)
- [x] Check pending reminders
- [x] Send reminders via Telegram
- [x] Mark reminders as sent
- [ ] Email reminders (future)
- [ ] Push notifications (future)

### Frontend Features
- [x] Auto-save notes
- [x] Optimistic note updates (instant UI)
- [x] Filter todos by completion status
- [x] Filter todos by priority
- [x] Filter notes by folder
- [x] Filter notes by archive status
- [x] Full-text search (PostgreSQL tsvector/tsquery)
- [ ] Bulk operations (future)

### API Polish
- [x] Proper error responses
- [x] Status codes (200, 201, 400, 404, 500)
- [x] Pagination support (future)
- [x] Query filtering standardized
- [ ] Rate limiting (future)

## Phase 3: Polish & Testing (5% Complete)

### Testing Infrastructure
- [ ] Unit tests (backend - pytest)
- [ ] Unit tests (frontend - Jest/RTL)
- [ ] Integration tests (API)
- [ ] E2E tests (Playwright - future)
- **Target**: 80%+ code coverage
- **Status**: Not started

### CI/CD Pipeline
- [ ] GitHub Actions workflow
- [ ] Automated linting (black, eslint)
- [ ] Type checking (mypy, tsc)
- [ ] Test execution on PR
- [ ] Automated deployment (future)
- **Status**: Not started

### Documentation
- [x] README.md
- [x] Project overview & PDR
- [x] Codebase summary
- [x] Code standards & conventions
- [x] System architecture
- [x] This roadmap
- [ ] API documentation (Swagger - auto-generated)
- [ ] Deployment guide (in progress)
- [ ] Design guidelines (in progress)
- [ ] Setup guide (in progress)

### Performance Optimization
- [ ] Database query analysis
- [ ] API response time monitoring
- [ ] Frontend performance budgets
- [ ] Code splitting optimization
- [ ] Static asset CDN
- **Status**: Not started

### Security Audit
- [ ] Input validation review
- [ ] CORS configuration review
- [ ] JWT handling review
- [ ] SQL injection prevention check
- [ ] XSS prevention check
- **Status**: Not started

## Phase 4: Advanced Features (60% Complete)

### User Experience
- [x] Full-text search on notes (PostgreSQL tsvector)
- [ ] Note templates
- [ ] Quick capture widget
- [x] Dark/light/system theme toggle (AZD-16)
- [ ] Note sharing (with permissions)
- [ ] Collaborative editing (real-time)

### Features
- [ ] Todo time tracking
- [x] Todo recurring (daily, weekly, monthly) (AZD-18)
- [x] Note export (Markdown, PDF, ZIP) (AZD-17)
- [ ] Data backup & restore
- [x] Tags/labels system for notes & todos (AZD-19)
- [ ] Analytics dashboard

### Performance & Quality
- [x] Database indexes optimization (AZD-13)
- [x] API pagination (limit/offset) (AZD-13)
- [x] API rate limiting (slowapi)
- [x] Backend test infrastructure (pytest, 22 tests)
- [x] Frontend test infrastructure (vitest)

### Mobile & Platforms
- [ ] React Native mobile app
- [ ] iOS app (native)
- [ ] Android app (native)
- [x] PWA/offline support (service worker, IndexedDB, sync) (AZD-20)
- [ ] Web clipper browser extension

### Integration
- [ ] Slack integration
- [ ] Discord bot integration
- [ ] WhatsApp integration
- [ ] Email sync (incoming)
- [ ] Calendar integration

### Backend Enhancements
- [ ] Redis caching layer
- [ ] Distributed task scheduling (Celery)
- [ ] Full-text search engine (Elasticsearch)
- [ ] Real-time WebSocket support
- [ ] GraphQL API (alternative to REST)

## Milestone Timeline

| Milestone | Phase | Target Date | Status |
|-----------|-------|-------------|--------|
| Core features complete | 1 | 2024-01-31 | Complete ✓ |
| Telegram integration & enhancements | 2 | 2026-02-14 | Complete ✓ |
| First beta release | 2 | 2026-03-15 | Planned |
| Test suite (50%+) | 3 | 2024-03-15 | Planned |
| CI/CD pipeline | 3 | 2024-03-31 | Planned |
| Production ready | 3 | 2024-04-30 | Planned |
| Full-text search | 4 | 2024-06-30 | Future |
| Mobile app v1 | 4 | 2024-09-30 | Future |

## Known Issues & Gaps

### Critical (Block Release)
- Production deployment not configured
- No error logging/monitoring
- Limited test coverage (backend: 22 tests, frontend: in progress)

### High Priority (Before v1)
- Reminders only via Telegram (no email/push notifications)
- No data backup/recovery process
- No user profile customization
- No note sharing/collaboration
- No audit logging

### Medium Priority (Future)
- No performance monitoring dashboard
- No Slack/Discord/WhatsApp integration
- Note templates not implemented
- No collaborative editing (real-time sync)

### Low Priority (Future)
- Mobile app (web-responsive only)
- Web clipper browser extension
- Calendar integration
- Email sync (incoming)

## Success Criteria

### Phase Completion
- All planned features implemented
- Code reviewed and merged
- Tests passing (once implemented)
- Documentation updated
- No critical bugs identified

### Release Readiness
- Test coverage > 80%
- All endpoints documented
- Deployment runbook created
- Security audit passed
- Performance targets met (API < 200ms p95)

## Dependencies & Constraints

### External
- Supabase (free tier: 2GB DB, 50k MAU)
- Telegram Bot API (free, rate-limited)
- AWS/GCP for hosting (future, ~$50-200/month)

### Internal
- Single developer (current)
- Limited DevOps infrastructure
- Manual deployment process
- No production monitoring yet

### Technical
- Python 3.13+ required
- Node.js 22+ required
- PostgreSQL 15+ required
- Bun 1.2.4+ package manager

## Resource Allocation

| Phase | Dev Time (est) | Priority | Owner |
|-------|----------------|----------|-------|
| Phase 1 | 40 hours | Critical | Michael |
| Phase 2 | 30 hours | High | Michael |
| Phase 3 | 40 hours | High | Michael |
| Phase 4 | 80+ hours | Low | TBD |

## Budget & Costs

| Item | Cost | Duration |
|------|------|----------|
| Supabase (free tier) | $0 | ∞ |
| Supabase (paid, if needed) | $25/month | TBD |
| VPS hosting | $10-50/month | TBD |
| Domain name | $12/year | TBD |
| Monitoring (Sentry) | $0 (free tier) | TBD |
| **Total** | **$0 - $90/month** | |

## How to Contribute

- Report bugs via GitHub Issues
- Request features with context
- Submit PRs with tests
- Improve documentation
- Share feedback on UX

## References

- Code Standards: [`docs/code-standards.md`](./code-standards.md)
- Architecture: [`docs/system-architecture.md`](./system-architecture.md)
- Overview & PDR: [`docs/project-overview-pdr.md`](./project-overview-pdr.md)
