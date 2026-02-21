/**
 * Notes store - manages notes CRUD operations with offline support.
 */

import { browser } from '$app/environment';
import { api } from '$lib/api';
import type { Note, PaginatedResponse, Tag } from '$lib/types';
import * as notesDB from '$lib/offline/indexed-db-notes';
import * as syncQueue from '$lib/offline/indexed-db-sync-queue';

export interface NoteCounts {
	total: number;
	by_folder: Record<string, number>;
	no_folder: number;
}

// Custom event for cross-store communication
const NOTES_CHANGED_EVENT = 'notesapp:notes-changed';

function emitNotesChanged() {
	if (browser) {
		window.dispatchEvent(new CustomEvent(NOTES_CHANGED_EVENT));
	}
}

export class NotesStore {
	notes = $state<Note[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);
	total = $state(0);
	fromCache = $state(false);
	counts = $state<NoteCounts | null>(null);

	private offset = 0;
	private limit = 50;
	private currentFolderId?: string;
	private currentSearch?: string;
	private currentTagIds?: string[];

	get hasMore() {
		return this.notes.length < this.total;
	}

	async fetchNotes(folderId?: string, search?: string, tagIds?: string[]) {
		this.loading = true;
		this.error = null;
		this.offset = 0;
		this.currentFolderId = folderId;
		this.currentSearch = search;
		this.currentTagIds = tagIds;

		try {
			const params = new URLSearchParams();
			if (folderId) params.set('folder_id', folderId);
			if (search) params.set('search', search);
			if (tagIds && tagIds.length > 0) params.set('tag_ids', tagIds.join(','));
			params.set('limit', this.limit.toString());
			params.set('offset', '0');
			const query = params.toString();
			const path = `/api/notes/${query ? `?${query}` : ''}`;

			const data = await api.get<PaginatedResponse<Note>>(path);
			this.notes = data.items;
			this.total = data.total;
			this.fromCache = false;

			// Write-through to IndexedDB
			await notesDB.putManyNotes(data.items).catch(console.error);

			// Notify sidebar to refresh counts (backend may have cleaned up empty notes)
			emitNotesChanged();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to fetch notes';
			this.error = message;

			// Offline fallback: load from IndexedDB
			if (browser && !navigator.onLine) {
				try {
					const cached = await notesDB.getAllNotes();
					this.notes = cached;
					this.total = cached.length;
					this.fromCache = true;
					this.error = null;
				} catch (cacheErr) {
					console.error('[notes-store] Failed to load from cache:', cacheErr);
				}
			}
		} finally {
			this.loading = false;
		}
	}

	async loadMore() {
		if (this.loading || !this.hasMore) return;

		this.loading = true;
		this.error = null;

		try {
			const newOffset = this.offset + this.limit;
			const params = new URLSearchParams();
			if (this.currentFolderId) params.set('folder_id', this.currentFolderId);
			if (this.currentSearch) params.set('search', this.currentSearch);
			if (this.currentTagIds && this.currentTagIds.length > 0)
				params.set('tag_ids', this.currentTagIds.join(','));
			params.set('limit', this.limit.toString());
			params.set('offset', newOffset.toString());
			const query = params.toString();
			const path = `/api/notes/${query ? `?${query}` : ''}`;

			const data = await api.get<PaginatedResponse<Note>>(path);
			this.notes = [...this.notes, ...data.items];
			this.total = data.total;
			this.offset = newOffset;

			await notesDB.putManyNotes(data.items).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to load more notes';
			this.error = message;
		} finally {
			this.loading = false;
		}
	}

	async createNote(data: Partial<Note>): Promise<Note> {
		// Offline: queue + local optimistic update
		if (browser && !navigator.onLine) {
			const tempNote: Note = {
				id: crypto.randomUUID(),
				user_id: '',
				title: data.title || '',
				content: data.content || '',
				folder_id: data.folder_id || null,
				is_pinned: data.is_pinned || false,
				is_archived: data.is_archived || false,
				tags: data.tags || [],
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			};
			await notesDB.putNote(tempNote);
			await syncQueue.enqueue({
				entity_type: 'note',
				operation: 'create',
				entity_id: tempNote.id,
				payload: data as Record<string, unknown>,
				timestamp: Date.now(),
				retry_count: 0
			});
			this.notes = [tempNote, ...this.notes];
			return tempNote;
		}

		// Online: normal API call + write-through
		try {
			const created = await api.post<Note>('/api/notes/', data);
			this.notes = [created, ...this.notes];
			await notesDB.putNote(created).catch(console.error);
			// Notify other stores that notes changed
			emitNotesChanged();
			return created;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create note';
			this.error = message;
			throw err;
		}
	}

	async updateNote(id: string, data: Partial<Note>): Promise<Note> {
		// Offline: queue + local optimistic update
		if (browser && !navigator.onLine) {
			const existing = await notesDB.getNoteById(id);
			if (!existing) throw new Error('Note not found in local cache');

			const updated: Note = { ...existing, ...data, updated_at: new Date().toISOString() };
			await notesDB.putNote(updated);
			await syncQueue.enqueue({
				entity_type: 'note',
				operation: 'update',
				entity_id: id,
				payload: data as Record<string, unknown>,
				timestamp: Date.now(),
				retry_count: 0
			});
			this.notes = this.notes.map((n) => (n.id === id ? updated : n));
			return updated;
		}

		// Online: normal API call + write-through
		try {
			const updated = await api.put<Note>(`/api/notes/${id}`, data);
			this.notes = this.notes.map((n) => (n.id === id ? updated : n));
			await notesDB.putNote(updated).catch(console.error);
			return updated;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to update note';
			this.error = message;
			throw err;
		}
	}

	/** Update note tags in local state (no API call - already done by editor). */
	updateNoteTags(noteId: string, tags: Tag[]): void {
		this.notes = this.notes.map((n) => (n.id === noteId ? { ...n, tags } : n));
	}

	async deleteNote(id: string): Promise<void> {
		// Offline: queue + local optimistic update
		if (browser && !navigator.onLine) {
			await notesDB.deleteNoteLocal(id);
			await syncQueue.enqueue({
				entity_type: 'note',
				operation: 'delete',
				entity_id: id,
				payload: null,
				timestamp: Date.now(),
				retry_count: 0
			});
			this.notes = this.notes.filter((n) => n.id !== id);
			return;
		}

		// Online: normal API call + write-through
		try {
			await api.delete(`/api/notes/${id}`);
			this.notes = this.notes.filter((n) => n.id !== id);
			await notesDB.deleteNoteLocal(id).catch(console.error);
			// Notify other stores that notes changed
			emitNotesChanged();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete note';
			this.error = message;
			throw err;
		}
	}

	async moveNoteToFolder(noteId: string, folderId: string | null): Promise<void> {
		try {
			await api.put(`/api/notes/${noteId}`, { folder_id: folderId });
			this.notes = this.notes.map((n) => (n.id === noteId ? { ...n, folder_id: folderId } : n));
			// Notify other stores that notes changed
			emitNotesChanged();
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to move note';
			this.error = message;
			throw err;
		}
	}

	async fetchNoteCounts(): Promise<void> {
		try {
			this.counts = await api.get<NoteCounts>('/api/notes/counts');
		} catch (err) {
			console.error('[notes-store] Failed to fetch counts:', err);
		}
	}

	/** Subscribe to note changes from other store instances. Returns cleanup function. */
	subscribeToChanges(): () => void {
		if (!browser) return () => {};

		const handler = () => {
			this.fetchNoteCounts();
		};
		window.addEventListener(NOTES_CHANGED_EVENT, handler);
		return () => window.removeEventListener(NOTES_CHANGED_EVENT, handler);
	}
}
