/**
 * Folders store - manages folder CRUD operations with tree structure.
 */

import { browser } from '$app/environment';
import { api } from '$lib/api';
import type { Folder, PaginatedResponse } from '$lib/types';
import * as foldersDB from '$lib/offline/indexed-db-folders';
import * as syncQueue from '$lib/offline/indexed-db-sync-queue';

function buildFolderTree(folders: Folder[]): Folder[] {
	const folderMap = new Map<string, Folder>();

	folders.forEach((folder) => {
		folderMap.set(folder.id, { ...folder, children: [] });
	});

	const roots: Folder[] = [];

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

export class FoldersStore {
	folders = $state<Folder[]>([]);
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

			const data = await api.get<PaginatedResponse<Folder>>(`/api/folders?${params}`);
			this.folders = data.items;
			this.total = data.total;
			this.fromCache = false;

			await foldersDB.putManyFolders(data.items).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to fetch folders';
			this.error = message;

			if (browser && !navigator.onLine) {
				try {
					const cached = await foldersDB.getAllFolders();
					this.folders = cached;
					this.total = cached.length;
					this.fromCache = true;
					this.error = null;
				} catch (cacheErr) {
					console.error('[folders-store] Failed to load from cache:', cacheErr);
				}
			}
		} finally {
			this.loading = false;
		}
	}

	async createFolder(name: string, parentId?: string): Promise<Folder> {
		if (browser && !navigator.onLine) {
			const tempFolder: Folder = {
				id: crypto.randomUUID(),
				user_id: '',
				name,
				parent_id: parentId || null,
				icon: null,
				children: [],
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			};
			await foldersDB.putFolder(tempFolder);
			await syncQueue.enqueue({
				entity_type: 'folder',
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
			const created = await api.post<Folder>('/api/folders', { name, parent_id: parentId });
			this.folders = [...this.folders, created];
			await foldersDB.putFolder(created).catch(console.error);
			return created;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create folder';
			this.error = message;
			throw err;
		}
	}

	async updateFolder(id: string, data: { name?: string; parent_id?: string | null }): Promise<Folder> {
		try {
			const updated = await api.put<Folder>(`/api/folders/${id}`, data);
			this.folders = this.folders.map((f) => (f.id === id ? updated : f));
			await foldersDB.putFolder(updated).catch(console.error);
			return updated;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to update folder';
			this.error = message;
			throw err;
		}
	}

	async deleteFolder(id: string): Promise<void> {
		try {
			await api.delete(`/api/folders/${id}`);
			this.folders = this.folders.filter((f) => f.id !== id);
			await foldersDB.deleteFolderLocal(id).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete folder';
			this.error = message;
			throw err;
		}
	}
}
