/**
 * Todo folders store - manages todo folder CRUD with tree structure.
 */

import { browser } from '$app/environment';
import { api } from '$lib/api';
import type { TodoFolder, TodoFolderStats, PaginatedResponse } from '$lib/types';
import * as todoFoldersDB from '$lib/offline/indexed-db-todo-folders';
import * as syncQueue from '$lib/offline/indexed-db-sync-queue';

function buildFolderTree(folders: TodoFolder[]): TodoFolder[] {
	const folderMap = new Map<string, TodoFolder>();

	folders.forEach((folder) => {
		folderMap.set(folder.id, { ...folder, children: [] });
	});

	const roots: TodoFolder[] = [];

	folderMap.forEach((folder) => {
		if (folder.parent_id) {
			const parent = folderMap.get(folder.parent_id);
			if (parent) {
				parent.children!.push(folder);
			} else {
				roots.push(folder);
			}
		} else {
			roots.push(folder);
		}
	});

	return roots;
}

export class TodoFoldersStore {
	folders = $state<TodoFolder[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);
	total = $state(0);
	fromCache = $state(false);

	private offset = 0;
	private limit = 50;

	get hasMore() {
		return this.folders.length < this.total;
	}

	get folderTree() {
		return buildFolderTree(this.folders);
	}

	async fetchFolders() {
		this.loading = true;
		this.error = null;
		this.offset = 0;

		try {
			const params = new URLSearchParams();
			params.set('limit', this.limit.toString());
			params.set('offset', '0');

			const data = await api.get<PaginatedResponse<TodoFolder>>(
				`/api/todo-folders/?${params}`
			);
			this.folders = data.items;
			this.total = data.total;
			this.fromCache = false;

			await todoFoldersDB.putManyTodoFolders(data.items).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to fetch todo folders';
			this.error = message;

			if (browser && !navigator.onLine) {
				try {
					const cached = await todoFoldersDB.getAllTodoFolders();
					this.folders = cached;
					this.total = cached.length;
					this.fromCache = true;
					this.error = null;
				} catch (cacheErr) {
					console.error('[todo-folders-store] Failed to load from cache:', cacheErr);
				}
			}
		} finally {
			this.loading = false;
		}
	}

	async createFolder(name: string, parentId?: string): Promise<TodoFolder> {
		if (browser && !navigator.onLine) {
			const tempFolder: TodoFolder = {
				id: crypto.randomUUID(),
				user_id: '',
				name,
				parent_id: parentId || null,
				sort_order: 0,
				children: [],
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			};
			await todoFoldersDB.putTodoFolder(tempFolder);
			await syncQueue.enqueue({
				entity_type: 'todo_folder',
				operation: 'create',
				entity_id: tempFolder.id,
				payload: { name, parent_id: parentId },
				timestamp: Date.now(),
				retry_count: 0
			});
			this.folders = [...this.folders, tempFolder];
			return tempFolder;
		}

		try {
			const created = await api.post<TodoFolder>('/api/todo-folders/', {
				name,
				parent_id: parentId
			});
			this.folders = [...this.folders, created];
			await todoFoldersDB.putTodoFolder(created).catch(console.error);
			return created;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create todo folder';
			this.error = message;
			throw err;
		}
	}

	async updateFolder(
		id: string,
		data: { name?: string; parent_id?: string | null; sort_order?: number }
	): Promise<TodoFolder> {
		try {
			const updated = await api.put<TodoFolder>(`/api/todo-folders/${id}`, data);
			this.folders = this.folders.map((f) => (f.id === id ? updated : f));
			await todoFoldersDB.putTodoFolder(updated).catch(console.error);
			return updated;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to update todo folder';
			this.error = message;
			throw err;
		}
	}

	async deleteFolder(id: string): Promise<void> {
		try {
			await api.delete(`/api/todo-folders/${id}`);
			this.folders = this.folders.filter((f) => f.id !== id);
			await todoFoldersDB.deleteTodoFolderLocal(id).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete todo folder';
			this.error = message;
			throw err;
		}
	}

	async fetchFolderStats(folderId: string): Promise<TodoFolderStats> {
		return api.get<TodoFolderStats>(`/api/todo-folders/${folderId}/stats`);
	}
}
