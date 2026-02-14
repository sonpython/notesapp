# Offline Storage Module

IndexedDB-based local storage for offline-first PWA functionality.

## Database Schema

**Database:** `notesapp-offline` (version 1)

### Stores

1. **notes** - Local cache of user notes
   - keyPath: `id`
   - indexes: `updated_at`, `folder_id`, `is_archived`

2. **todos** - Local cache of user todos
   - keyPath: `id`
   - indexes: `updated_at`, `is_completed`, `parent_id`

3. **folders** - Local cache of user folders
   - keyPath: `id`
   - indexes: `updated_at`, `parent_id`

4. **sync-queue** - Pending mutations to sync with server
   - keyPath: `id` (auto-increment)
   - indexes: `timestamp`, `entity_type`

5. **meta** - Metadata (last sync timestamps, etc.)
   - keyPath: `key`

## Usage

### Notes Store
```typescript
import { getAllNotes, getNoteById, putNote, putManyNotes, deleteNoteLocal, clearNotes } from '@/lib/offline/indexed-db-notes';

// Get all notes
const notes = await getAllNotes();

// Get single note
const note = await getNoteById('uuid-here');

// Save single note
await putNote({ id: '...', title: 'Test', ... });

// Bulk save
await putManyNotes([note1, note2, note3]);

// Delete note
await deleteNoteLocal('uuid-here');

// Clear all notes
await clearNotes();
```

### Todos Store
```typescript
import { getAllTodos, getTodoById, putTodo, putManyTodos, deleteTodoLocal, clearTodos } from '@/lib/offline/indexed-db-todos';
```

### Folders Store
```typescript
import { getAllFolders, getFolderById, putFolder, putManyFolders, deleteFolderLocal, clearFolders } from '@/lib/offline/indexed-db-folders';
```

### Sync Queue
```typescript
import { enqueue, getAllPending, dequeue, updateRetryCount, clearQueue } from '@/lib/offline/indexed-db-sync-queue';

// Add mutation to queue
await enqueue({
  entity_type: 'note',
  operation: 'create',
  entity_id: 'uuid-here',
  payload: { title: 'New Note', content: '...' },
  timestamp: Date.now(),
  retry_count: 0
});

// Get all pending operations
const pending = await getAllPending();

// Remove from queue after successful sync
await dequeue(entryId);

// Increment retry count on failure
await updateRetryCount(entryId, 1);
```

### Meta Store
```typescript
import { setMeta, getMeta } from '@/lib/offline/indexed-db-client';

// Save last sync timestamp
await setMeta('last_sync_notes', Date.now());

// Retrieve last sync
const lastSync = await getMeta('last_sync_notes');
```

### Clear All Data (Logout)
```typescript
import { clearAllStores } from '@/lib/offline/indexed-db-client';

await clearAllStores();
```

## Manual Testing in Browser

Open DevTools > Application > Storage > IndexedDB > notesapp-offline

### Test in Console
```javascript
// Import modules (works in Next.js dev environment)
const { putNote, getAllNotes } = await import('@/lib/offline/indexed-db-notes');

// Save test note
await putNote({
  id: crypto.randomUUID(),
  user_id: 'test-user',
  title: 'Test Note',
  content: 'This is a test',
  folder_id: null,
  is_pinned: false,
  is_archived: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  tags: []
});

// Retrieve all notes
const notes = await getAllNotes();
console.log(notes);
```

## Architecture Notes

- **Singleton pattern**: `getDB()` ensures single connection
- **Type safety**: All operations use types from `@/lib/types`
- **Transaction batching**: `putMany*` methods use transactions for atomicity
- **Async/await**: All operations are promise-based
- **Indexed queries**: Efficient lookups by `updated_at`, `folder_id`, etc.

## Next Steps (Phase 3)

- Create offline-first hooks that read from IndexedDB first
- Implement background sync to server
- Add conflict resolution logic
