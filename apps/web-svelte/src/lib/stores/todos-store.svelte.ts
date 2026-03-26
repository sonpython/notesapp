/**
 * Todos store - manages todo CRUD operations with offline support.
 */

import { browser } from '$app/environment';
import { api } from '$lib/api';
import type { Todo, PaginatedResponse } from '$lib/types';
import * as todosDB from '$lib/offline/indexed-db-todos';
import * as syncQueue from '$lib/offline/indexed-db-sync-queue';

export type TodoFilter = 'all' | 'active' | 'completed' | 'overdue';

interface CreateTodoData {
	title: string;
	description?: string;
	priority?: number;
	deadline?: string;
	parent_id?: string;
	folder_id?: string;
	reminder_at?: string;
	recurrence_type?: string;
	recurrence_interval?: number;
	recurrence_days?: string;
	recurrence_end_date?: string;
}

interface UpdateTodoData {
	title?: string;
	description?: string;
	priority?: number;
	deadline?: string;
	is_completed?: boolean;
	reminder_at?: string;
	recurrence_type?: string;
	recurrence_interval?: number;
	recurrence_days?: string;
	recurrence_end_date?: string;
}

export class TodosStore {
	todos = $state<Todo[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);
	filter = $state<TodoFilter>('all');
	total = $state(0);
	fromCache = $state(false);
	counts = $state<{ total: number; active: number; completed: number }>({ total: 0, active: 0, completed: 0 });

	private offset = 0;
	private limit = 50;
	private currentTagIds?: string[];
	private currentFolderId?: string;

	get hasMore() {
		return this.todos.length < this.total;
	}

	/** Fetch todo counts for sidebar display */
	async fetchCounts(folderId?: string) {
		try {
			const params = folderId ? `?folder_id=${folderId}` : '';
			const data = await api.get<{ total: number; active: number; completed: number }>(`/api/todos/counts${params}`);
			this.counts = data;
		} catch {
			// Silently fail - counts are non-critical
		}
	}

	async fetchTodos(activeFilter?: TodoFilter, tagIds?: string[], folderId?: string) {
		this.loading = true;
		this.error = null;
		this.offset = 0;
		this.currentTagIds = tagIds;
		this.currentFolderId = folderId;

		try {
			const filterParam = activeFilter || this.filter;
			const params = new URLSearchParams();
			// Convert filter to backend params
			if (filterParam === 'active') {
				params.set('is_completed', 'false');
			} else if (filterParam === 'completed') {
				params.set('is_completed', 'true');
			} else if (filterParam === 'overdue') {
				params.set('is_completed', 'false');
				params.set('has_deadline', 'true');
				params.set('overdue', 'true');
			}
			// 'all' sends no filter params
			if (folderId) params.set('folder_id', folderId);
			if (tagIds && tagIds.length > 0) params.set('tag_ids', tagIds.join(','));
			params.set('limit', this.limit.toString());
			params.set('offset', '0');
			const query = params.toString();

			const data = await api.get<PaginatedResponse<Todo>>(`/api/todos/${query ? `?${query}` : ''}`);
			this.todos = data.items;
			this.total = data.total;
			this.fromCache = false;

			await todosDB.putManyTodos(data.items).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to fetch todos';
			this.error = message;

			if (browser && !navigator.onLine) {
				try {
					const cached = await todosDB.getAllTodos();
					this.todos = cached;
					this.total = cached.length;
					this.fromCache = true;
					this.error = null;
				} catch (cacheErr) {
					console.error('[todos-store] Failed to load from cache:', cacheErr);
				}
			}
		} finally {
			this.loading = false;
		}
	}

	async createTodo(data: CreateTodoData): Promise<Todo> {
		if (browser && !navigator.onLine) {
			const tempTodo: Todo = {
				id: crypto.randomUUID(),
				user_id: '',
				title: data.title,
				description: data.description || null,
				priority: data.priority ?? 2,
				deadline: data.deadline || null,
				is_completed: false,
				completed_at: null,
				parent_id: data.parent_id || null,
				note_id: null,
				folder_id: data.folder_id || null,
				children: [],
				sort_order: 0,
				reminder_at: data.reminder_at || null,
				reminder_sent: false,
				recurrence_type: data.recurrence_type || null,
				recurrence_interval: data.recurrence_interval || null,
				recurrence_days: data.recurrence_days || null,
				recurrence_end_date: data.recurrence_end_date || null,
				recurrence_parent_id: null,
				tags: [],
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			};
			await todosDB.putTodo(tempTodo);
			await syncQueue.enqueue({
				entity_type: 'todo',
				operation: 'create',
				entity_id: tempTodo.id,
				payload: data as unknown as Record<string, unknown>,
				timestamp: Date.now(),
				retry_count: 0
			});
			// If subtask, add to parent's children; otherwise add to top-level
			if (data.parent_id) {
				this.todos = this.addToParentChildren(this.todos, data.parent_id, tempTodo);
			} else {
				this.todos = [tempTodo, ...this.todos];
			}
			return tempTodo;
		}

		try {
			const created = await api.post<Todo>('/api/todos/', data);
			// If subtask, add to parent's children; otherwise add to top-level
			if (data.parent_id) {
				this.todos = this.addToParentChildren(this.todos, data.parent_id, created);
			} else {
				this.todos = [created, ...this.todos];
			}
			await todosDB.putTodo(created).catch(console.error);
			return created;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create todo';
			this.error = message;
			throw err;
		}
	}

	/** Recursively add a todo to its parent's children array */
	private addToParentChildren(todos: Todo[], parentId: string, newTodo: Todo): Todo[] {
		return todos.map((t) => {
			if (t.id === parentId) {
				return { ...t, children: [...(t.children || []), newTodo] };
			}
			if (t.children?.length) {
				return { ...t, children: this.addToParentChildren(t.children, parentId, newTodo) };
			}
			return t;
		});
	}

	async updateTodo(id: string, data: UpdateTodoData): Promise<Todo> {
		try {
			const updated = await api.put<Todo>(`/api/todos/${id}`, data);
			// Update state recursively to handle nested children
			this.todos = this.updateTodoRecursively(this.todos, id, updated);
			await todosDB.putTodo(updated).catch(console.error);
			return updated;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to update todo';
			this.error = message;
			throw err;
		}
	}

	async toggleTodo(id: string): Promise<Todo> {
		this.error = null;

		// Offline: queue + local optimistic update
		if (browser && !navigator.onLine) {
			const target = this.findTodoById(this.todos, id);
			if (!target) {
				this.error = 'Todo not found in local cache';
				throw new Error('Todo not found');
			}
			const updated: Todo = {
				...target,
				is_completed: !target.is_completed,
				completed_at: !target.is_completed ? new Date().toISOString() : null,
				updated_at: new Date().toISOString()
			};
			await todosDB.putTodo(updated);
			await syncQueue.enqueue({
				entity_type: 'todo',
				operation: 'update',
				entity_id: id,
				payload: { is_completed: updated.is_completed },
				timestamp: Date.now(),
				retry_count: 0
			});
			// Update state recursively
			this.todos = this.updateTodoRecursively(this.todos, id, updated);
			return updated;
		}

		// Online: use dedicated toggle endpoint (handles nested children correctly)
		try {
			const todo = await api.post<Todo>(`/api/todos/${id}/toggle`);
			// Update state recursively
			this.todos = this.updateTodoRecursively(this.todos, id, todo);
			await todosDB.putTodo(todo).catch(console.error);
			return todo;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to toggle todo';
			this.error = message;
			throw err;
		}
	}

	/** Recursively find a todo by ID in nested structure */
	private findTodoById(todos: Todo[], id: string): Todo | undefined {
		for (const todo of todos) {
			if (todo.id === id) return todo;
			if (todo.children?.length) {
				const found = this.findTodoById(todo.children, id);
				if (found) return found;
			}
		}
		return undefined;
	}

	/** Recursively update a todo by ID in nested structure, preserving children */
	private updateTodoRecursively(todos: Todo[], id: string, updated: Todo): Todo[] {
		return todos.map((t) => {
			if (t.id === id) {
				// Preserve children from original todo (API response doesn't include them)
				return { ...updated, children: t.children };
			}
			if (t.children?.length) {
				return { ...t, children: this.updateTodoRecursively(t.children, id, updated) };
			}
			return t;
		});
	}

	async deleteTodo(id: string): Promise<void> {
		try {
			await api.delete(`/api/todos/${id}`);
			// Remove todo from list (handles both top-level and nested children)
			this.todos = this.removeTodoRecursively(this.todos, id);
			await todosDB.deleteTodoLocal(id).catch(console.error);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to delete todo';
			this.error = message;
			throw err;
		}
	}

	/** Recursively remove a todo by ID from nested structure */
	private removeTodoRecursively(todos: Todo[], id: string): Todo[] {
		return todos
			.filter((t) => t.id !== id)
			.map((t) => ({
				...t,
				children: t.children ? this.removeTodoRecursively(t.children, id) : []
			}));
	}

	/** Reorder todos by providing new ordered array */
	async reorderTodos(orderedIds: string[]): Promise<boolean> {
		this.error = null;

		// Build reorder request
		const items = orderedIds.map((id, index) => ({ id, sort_order: index }));

		// Optimistic update — reorder incomplete, keep completed appended
		const prev = this.todos;
		const reorderedSet = new Set(orderedIds);
		const reordered = orderedIds
			.map((id) => prev.find((t) => t.id === id))
			.filter((t): t is Todo => t !== undefined);
		const remaining = prev.filter((t) => !reorderedSet.has(t.id));
		this.todos = [...reordered, ...remaining];

		try {
			await api.put('/api/todos/reorder', { items });
			return true;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to reorder todos';
			this.error = message;
			// Revert with current filter context (preserve folder/tag filter)
			await this.fetchTodos(this.filter, this.currentTagIds, this.currentFolderId);
			return false;
		}
	}
}
