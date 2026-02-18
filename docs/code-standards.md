# Code Standards & Conventions

## File Naming

### Backend (Python)
- Use **snake_case** for all file names
- Descriptive names: `note_query_service.py`, `telegram_service.py` (not `service.py`)
- Model files: `note.py`, `todo.py`, `folder.py`
- Router files: `auth.py`, `notes.py`, `folders.py`
- Service files: `note_query_service.py`, `todo_query_service.py`, `reminder_service.py`
- Keep under 200 lines; split if larger

### Frontend (TypeScript/React)
- Use **kebab-case** for file names (Next.js convention)
- Component files: `app-header.tsx`, `note-editor.tsx`, `todo-item.tsx`
- Hook files: `use-auth.ts`, `use-debounce.ts`, `use-notes.ts`
- Utility files: `supabase-browser.ts`, `api.ts`, `types.ts`
- Keep under 200 lines; extract logic to separate modules

## Naming Conventions

### Python
- **Variables**: snake_case (`user_id`, `created_at`, `is_archived`)
- **Functions**: snake_case (`get_notes()`, `create_user()`)
- **Classes**: PascalCase (`Note`, `TodoQueryService`, `ApiClient`)
- **Constants**: UPPER_SNAKE_CASE (`API_URL`, `DEFAULT_TIMEOUT`)
- **Private/internal**: Prefix with underscore (`_ensure_async_url()`, `_bearer_scheme`)

### TypeScript/React
- **Variables**: camelCase (`userId`, `createdAt`, `isArchived`)
- **Functions**: camelCase (`getNotes()`, `createUser()`)
- **Types/Interfaces**: PascalCase (`Note`, `Todo`, `ApiClient`)
- **Constants**: UPPER_SNAKE_CASE or camelCase (`API_URL`, `defaultTimeout`)
- **React Components**: PascalCase (`AppHeader`, `NoteEditor`, `TodoItem`)
- **Custom Hooks**: camelCase with `use` prefix (`useAuth`, `useNotes`, `useDebounce`)

## Casing by Data Type

### Database & API Fields
Always use **snake_case** in database and API responses (Python/database standard):
```json
{
  "user_id": "uuid",
  "created_at": "2024-02-14T10:00:00Z",
  "is_archived": false,
  "folder_id": null
}
```

### TypeScript Interfaces
Match database field names exactly (snake_case):
```typescript
export interface Note {
  id: string
  user_id: string
  title: string
  created_at: string
  is_archived: boolean
}
```

### JavaScript Objects & Props
Use camelCase in component props and local variables:
```typescript
const { userId, createdAt, isArchived } = note
const handleNoteUpdate = (newTitle: string) => { ... }
```

## Code Organization

### Backend Module Structure
```
app/
├── main.py                    # Entry point
├── config.py                  # Settings
├── database.py                # ORM setup
├── deps.py                    # Dependencies (auth)
├── models/
│   ├── __init__.py
│   ├── note.py
│   ├── todo.py
│   └── folder.py
├── schemas/
│   ├── __init__.py
│   ├── note.py                # Request/response schemas
│   └── todo.py
├── routers/                   # API endpoints
│   ├── __init__.py
│   ├── auth.py
│   ├── notes.py
│   └── todos.py
├── services/                  # Business logic
│   ├── __init__.py
│   ├── note_query_service.py
│   ├── todo_query_service.py
│   └── reminder_service.py
└── tasks/                     # Background jobs
    ├── __init__.py
    └── reminders.py
```

### Frontend Module Structure
```
src/
├── app/                       # Next.js pages
│   ├── (app)/                 # Protected routes
│   │   ├── notes/
│   │   ├── todos/
│   │   └── settings/
│   ├── login/
│   ├── signup/
│   └── page.tsx               # Landing
├── components/
│   ├── layout/                # Shared layouts
│   ├── notes/                 # Note-specific
│   └── todos/                 # Todo-specific
├── hooks/                     # Custom React hooks
├── lib/                       # Utilities
│   ├── api.ts                 # API client
│   ├── types.ts               # Shared types
│   └── supabase-*.ts
├── middleware.ts
└── globals.css
```

## Coding Style

### Python

**Type Hints (mandatory for functions)**
```python
async def get_notes(user_id: str, db: AsyncSession) -> list[Note]:
    """Fetch all notes for a user."""
    ...

def _ensure_async_url(url: str) -> str:
    """Ensure database URL uses asyncpg driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url
```

**Docstrings (PEP 257)**
```python
def create_note(title: str, content: str) -> Note:
    """Create a new note.

    Args:
        title: Note title
        content: Note content (Markdown)

    Returns:
        The created Note object with ID
    """
```

**Error Handling**
```python
from fastapi import HTTPException, status

try:
    note = await db.get(Note, note_id)
except Exception as e:
    logger.error(f"Failed to fetch note {note_id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch note"
    )
```

**Imports: Group in order**
```python
# 1. Standard library
import logging
from typing import Optional

# 2. Third-party
import sqlalchemy as sa
from fastapi import Depends

# 3. Local
from app.database import get_db
from app.models import Note
```

**Max Line Length**: 100 characters

### TypeScript/React

**Type Annotations (mandatory)**
```typescript
interface Note {
  id: string
  user_id: string
  title: string
  content: string
  is_archived: boolean
}

const getNotes = async (userId: string): Promise<Note[]> => {
  const response = await fetch(`/api/notes?user_id=${userId}`)
  return response.json()
}
```

**JSX Component Structure**
```typescript
interface NoteEditorProps {
  noteId: string
  onSave: (content: string) => void
}

export const NoteEditor: React.FC<NoteEditorProps> = ({ noteId, onSave }) => {
  const [content, setContent] = useState("")

  const handleSave = useCallback(() => {
    onSave(content)
  }, [content, onSave])

  return (
    <div className="note-editor">
      {/* Component JSX */}
    </div>
  )
}
```

**Error Handling**
```typescript
try {
  const note = await api.get<Note>(`/api/notes/${noteId}`)
  setNote(note)
} catch (error) {
  console.error("Failed to load note:", error)
  toast.error("Could not load note. Please try again.")
}
```

**Max Line Length**: 100 characters

## API Design

### Endpoint Naming
- **Resources**: `/api/{resource}` (lowercase, plural)
  - `/api/notes` (list), `/api/notes/{id}` (detail)
  - `/api/folders`, `/api/todos`, `/api/images`
- **Actions**: POST `/api/{resource}/{id}/{action}`
  - `/api/todos/{id}/toggle` (complete/incomplete)
- **File Upload**: POST `/api/{resource}/upload` (multipart/form-data)
  - `/api/images/upload` (image file + metadata)

### Request/Response Format

**Request Body**
```json
{
  "title": "My Note",
  "content": "Note content",
  "folder_id": "uuid-string"
}
```

**Response Format**
```json
{
  "id": "uuid-string",
  "user_id": "uuid-string",
  "title": "My Note",
  "content": "Note content",
  "folder_id": "uuid-string",
  "created_at": "2024-02-14T10:00:00Z",
  "updated_at": "2024-02-14T10:00:00Z"
}
```

**File Upload Request (Image)**
```
POST /api/images/upload
Content-Type: multipart/form-data

file: <binary image data>
filename: screenshot.png (optional, extracted from file)
```

**File Upload Response**
```json
{
  "id": "uuid-string",
  "filename": "screenshot.png",
  "size_bytes": 204800,
  "mime_type": "image/png",
  "url": "/api/images/{id}",
  "created_at": "2024-02-14T10:00:00Z"
}
```

**Error Response**
```json
{
  "detail": "Note not found"
}
```

**File Upload Error Response**
```json
{
  "detail": "File size exceeds maximum (10MB)"
}
```
or
```json
{
  "detail": "File type not supported. Allowed: jpeg, png, gif, webp, svg+xml"
}
```

### Status Codes
- **200**: Success (GET, PUT, DELETE)
- **201**: Created (POST)
- **400**: Bad request (validation error)
- **401**: Unauthorized (missing/invalid token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not found
- **500**: Server error

## Database Design

### Naming Conventions
- **Table names**: snake_case, plural (`notes`, `todos`, `folders`)
- **Column names**: snake_case (`user_id`, `created_at`, `is_archived`)
- **Primary keys**: `id` (UUID with gen_random_uuid() default)
- **Foreign keys**: `{resource}_id` (e.g., `user_id`, `folder_id`, `note_id`)
- **Boolean fields**: `is_{state}` (e.g., `is_archived`, `is_completed`)
- **Timestamps**: `created_at`, `updated_at` (DateTime with timezone)

### Indexing Strategy
```python
# Always index user_id for fast filtering
user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

# Index foreign keys for joins
folder_id: Mapped[uuid.UUID | None] = mapped_column(
    sa.Uuid,
    sa.ForeignKey("folders.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)
```

### Relationships
- Use SQLAlchemy `relationship()` with `back_populates`
- Enable cascading deletes where appropriate
- Use `passive_deletes=True` for FK constraints

## Testing Standards

### Not Currently Implemented
- Unit tests: 0% coverage
- Integration tests: None
- E2E tests: Manual only

### Future Standards (To Implement)
- Backend: pytest + pytest-asyncio for async tests
- Frontend: Jest + React Testing Library
- Target: 80%+ code coverage
- Test organization: mirror source structure (`tests/app/models/`, `tests/hooks/`)

## Documentation Standards

### Code Comments
- Comment complex logic, not obvious code
- Avoid stating what the code does; explain why
- Example:
```python
# Good: Explains the why
# Use gen_random_uuid() instead of uuid4() for PostgreSQL compatibility
id: Mapped[uuid.UUID] = mapped_column(
    sa.Uuid,
    primary_key=True,
    server_default=sa.text("gen_random_uuid()"),
)

# Bad: States the obvious
# Set primary key to id
id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
```

### Docstring Format (Python)
```python
def create_note(title: str, content: str, user_id: str) -> Note:
    """Create a new note for the user.

    Args:
        title: Note title (max 255 chars)
        content: Note content in Markdown
        user_id: Owner's user ID

    Returns:
        The created Note with generated UUID and timestamps

    Raises:
        ValueError: If title is empty
    """
```

### JSDoc Format (TypeScript)
```typescript
/**
 * Fetch all notes for the current user.
 * @param filters - Optional filtering options
 * @returns Array of notes sorted by updated_at desc
 */
const fetchNotes = async (filters?: NoteFilters): Promise<Note[]> => {
  ...
}
```

## Dependency Management

### Python (uv)
- Use `pyproject.toml` (no requirements.txt)
- Pin versions for stability: `fastapi==0.104.1`
- Minimal dependencies: FastAPI, SQLAlchemy, Pydantic only
- Command: `uv sync` (install), `uv add package` (add)

### Node.js (Bun)
- Use `bun` (no npm, pnpm, or yarn)
- `package.json` for monorepo root and workspaces
- Lock file: `bun.lockb` (auto-generated, commit to git)
- Commands: `bun install`, `bun add package`, `bun run <script>`
- Filter workspaces: `bun --filter @notesapp/web-svelte install`

## Git & Commit Standards

### Branch Naming
- Feature: `feature/user-authentication`
- Fix: `fix/note-save-bug`
- Docs: `docs/deployment-guide`

### Commit Messages (Conventional)
```
feat(notes): add auto-save functionality
fix(auth): handle expired tokens correctly
docs: update API documentation
refactor(todos): extract query logic to service
test: add unit tests for reminder service
```

### Before Committing
- [ ] No console.log() or print() statements (debugging removed)
- [ ] Type checks pass: mypy (backend), tsc (frontend)
- [ ] Linting passes: black/ruff (backend), eslint (frontend)
- [ ] Tests pass (once implemented)
- [ ] No hardcoded secrets or API keys

## Security Standards

### Authentication
- All endpoints except `/api/health` and `/api/telegram/webhook` require Bearer token
- JWT validated via JWKS or symmetric key
- User ID extracted from token sub claim and verified

### Authorization
- All database queries filtered by `user_id` from token
- No cross-user data access
- Passwords hashed by Supabase (never handle directly)

### Input Validation
- Pydantic schemas validate all request bodies (backend)
- Field max lengths enforced (title: 255, content: unlimited)
- Enum validation for priority, status fields

### Output Sanitization
- React auto-escapes JSX content (XSS prevention)
- Markdown rendered safely via react-markdown (no HTML execution)
- Never return sensitive fields (password, JWT secret)

## Performance Standards

### API Response Target
- p95: < 200ms
- No N+1 queries (use eager loading)
- Connection pooling enabled (pool_pre_ping=True)

### Frontend Performance
- Page load: < 2s (3G network)
- Interactive: < 3s
- Code splitting: route-based, component lazy-loading
- No blocking scripts

### Database Optimization
- Indexed queries: user_id always indexed
- Lazy loading: related data loaded on demand
- Query batching: fetch multiple items in single query

## Error Handling Standards

### Backend Error Responses
```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Note title cannot be empty"
)
```

### File Upload Error Handling
```python
# Validate file size
if file.size > MINIO_MAX_IMAGE_SIZE:
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File size exceeds maximum ({MINIO_MAX_IMAGE_SIZE // 1024 // 1024}MB)"
    )

# Validate file type
if file.content_type not in ALLOWED_MIME_TYPES:
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail=f"File type not supported. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
    )

# Handle storage errors
try:
    await minio_service.upload_image(user_id, file)
except Exception as e:
    logger.error(f"Image upload failed: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to upload image. Please try again."
    )
```

### Frontend Error Handling
```typescript
if (!response.ok) {
  const error = await response.json()
  throw new Error(error.detail || "Unknown error")
}
```

### Logging Standards
- Use `logger = logging.getLogger(__name__)` in Python
- Log at appropriate levels: DEBUG, INFO, WARNING, ERROR
- Don't log sensitive data (passwords, tokens)
- Include context: function name, user ID (non-PII)

## Accessibility Standards (Future)

- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast: WCAG AA minimum
- Focus visible state on all buttons

## Performance Monitoring (Future)

- APM: Sentry for error tracking
- Analytics: User behavior tracking
- Metrics: API latency, error rate, uptime
