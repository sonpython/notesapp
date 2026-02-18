# Data Flows & Deployment Architecture

> Split from `system-architecture.md` for maintainability. See [system-architecture.md](./system-architecture.md) for core architecture.

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

### Image Upload & Serving Flow

```
User drops/pastes image in note editor (Browser)
  │
  ├─ codemirror-image-drop-extension.ts
  │  └─ image-upload-service.ts
  │     ├─ Validate file type (jpeg, png, gif, webp, svg+xml)
  │     ├─ Validate file size (max 10MB)
  │     └─ Show upload progress indicator
  │
  ▼ HTTP Request (multipart/form-data)

  /api/images/upload [POST]
  ├─ deps.get_current_user (JWT validation)
  │  └─ Extract user_id from token.sub
  │
  ├─ Validate multipart form data
  │  └─ Check file type & size
  │
  ├─ minio_storage_service.upload_image()
  │  ├─ Generate UUID for image: {uuid}.{ext}
  │  ├─ Upload to MinIO bucket
  │  │  └─ Key: users/{user_id}/images/{uuid}.{ext}
  │  ├─ Set object metadata (filename, mime type)
  │  └─ Return image_id (UUID)
  │
  └─ Response
     └─ ImageUploadResponse { id, url, size_bytes }

Browser receives image ID
  │
  ├─ Insert markdown: ![alt](/api/images/{id})
  │
  └─ Save note (auto-save triggered)

Serving Image (GET /api/images/{id})
  │
  ├─ deps.get_current_user (auth required)
  │
  ├─ minio_storage_service.get_image()
  │  ├─ Verify ownership: object key matches user_id
  │  ├─ Fetch from MinIO
  │  └─ Return file stream + metadata
  │
  ├─ Response
  │  ├─ HTTP 200 with image data
  │  ├─ Content-Type: image/*
  │  └─ Cache-Control: private, max-age=86400 (1 day)
  │
  └─ Browser displays image in note
```

### Authentication & Session Flow

```
User Signup/Login (Passkey WebAuthn)
  │
  ├─ Frontend
  │  └─ auth-api.ts
  │     └─ WebAuthn passkey flow
  │
  ├─ Backend validates passkey
  │  └─ Returns HS256 JWT
  │
  ├─ Frontend stores token
  │  └─ Secure httpOnly cookie
  │
  ├─ API call with Bearer token
  │  └─ Authorization: Bearer <jwt>
  │
  ├─ Backend JWT validation
  │  └─ deps.py get_current_user()
  │  ├─ Check HS256 algorithm
  │  ├─ Verify with JWT_SECRET
  │  └─ Extract user_id from sub claim
  │
  └─ Request proceeds with user context
     └─ All queries filtered by user_id
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

## Background Task Scheduling

### APScheduler Configuration
```
Interval: Every 60 seconds
Task: check_pending_reminders()
Concurrency: Single process (no distribution)
Persistence: In-memory (lost on restart)
```

### Reminder Checking Logic
1. Query todos with reminder_at <= NOW() and reminder_sent = false
2. Filter by user_id
3. Check if Telegram linked for user
4. Send message to Telegram chat_id
5. Mark as sent: UPDATE todos SET reminder_sent = true
6. Log result (success/failure)

## Deployment Architecture

### Production Setup
```
                    User Browser
                         │
                         ▼
                    ┌─────────────┐
                    │  Vercel/CDN │ (Static frontend)
                    │ (SvelteKit) │
                    └──────┬──────┘
                           │ API calls
                           ▼
                    ┌────────────────┐
                    │  Load Balancer │ (nginx/AWS ALB)
                    └────────┬───────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
      ┌─────────┐      ┌─────────┐      ┌─────────┐
      │ FastAPI │      │ FastAPI │      │ FastAPI │
      │  (Pod 1)│      │ (Pod 2) │      │  (Pod 3)│
      └────┬────┘      └────┬────┘      └────┬────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     ┌──────────────────┐       ┌──────────────────┐
     │  PostgreSQL      │       │  MinIO           │
     │  (Managed)       │       │  (S3-compatible) │
     └──────────────────┘       └──────────────────┘
```

## Performance Optimization

### Query Optimization
- Index user_id on all tables (fast filtering)
- Eager load related data (avoid N+1)
- Use connection pooling (session mode)
- Batch operations where possible

### Frontend Optimization
- Code splitting by route
- Lazy load components
- Debounce auto-save (500ms)
- Optimistic UI updates (no wait for server)

### Caching Strategy (Future)
- Redis for session cache
- CDN for static assets
- Query result caching (1 hour)
- Browser cache headers

## Scalability Considerations

### Horizontal Scaling
- Stateless FastAPI instances (no session affinity needed)
- Load balancer distributes requests
- Each instance connects to shared database

### Vertical Scaling
- Increase container memory (API)
- Increase database connection pool
- Upgrade PostgreSQL instance size

### Bottlenecks
- Database connection pool (currently: 5-20 connections)
- APScheduler runs in single process (no distributed scheduling)
- No caching layer (every read hits database)

## Security Architecture

### Data Isolation
- All queries filtered by user_id from JWT
- No cross-user data access possible
- Images isolated by user_id prefix in MinIO

### Token Management
- JWT stored in secure httpOnly cookies
- Automatic refresh before expiry
- CORS restricts origin access
- CSRF protection via SameSite cookies

### Input Validation
- Pydantic validates all request bodies
- SQL injection prevented via ORM parameterization
- XSS prevented via Svelte auto-escaping
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
