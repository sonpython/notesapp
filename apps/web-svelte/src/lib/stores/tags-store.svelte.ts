/**
 * Tags store - manages tag CRUD operations.
 */

import { api } from '$lib/api';
import type { Tag, PaginatedResponse } from '$lib/types';

export class TagsStore {
	tags = $state<Tag[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	async fetchTags() {
		this.loading = true;
		this.error = null;

		try {
			// Backend returns array directly, not paginated
			const data = await api.get<Tag[]>('/api/tags/');
			this.tags = data;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to fetch tags';
			this.error = message;
		} finally {
			this.loading = false;
		}
	}

	async createTag(name: string, color?: string): Promise<Tag> {
		try {
			const created = await api.post<Tag>('/api/tags/', { name, color });
			this.tags = [...this.tags, created];
			return created;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create tag';
			this.error = message;
			throw err;
		}
	}

	async updateTag(id: string, data: { name?: string; color?: string }): Promise<Tag> {
		try {
			const updated = await api.put<Tag>(`/api/tags/${id}`, data);
			this.tags = this.tags.map((t) => (t.id === id ? updated : t));
			return updated;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to update tag';
			this.error = message;
			throw err;
		}
	}

	async deleteTag(id: string): Promise<void> {
		try {
			await api.delete(`/api/tags/${id}`);
			this.tags = this.tags.filter((t) => t.id !== id);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete tag';
			this.error = message;
			throw err;
		}
	}
}

// Singleton instance for shared state across components
export const tagsStore = new TagsStore();
