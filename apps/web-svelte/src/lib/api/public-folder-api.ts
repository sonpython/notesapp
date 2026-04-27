/**
 * API client for the public shared todo folder endpoints.
 *
 * Always uses relative URLs and `credentials: 'include'` so the per-pub_id
 * share session cookie is sent on every mutation.
 */

export interface SharedFolderTodo {
	id: string;
	parent_id: string | null;
	title: string;
	description: string | null;
	is_completed: boolean;
	completed_at: string | null;
	deadline: string | null;
	priority: number;
	sort_order: number;
	created_at: string;
	updated_at: string;
	children: SharedFolderTodo[];
}

export interface SharedFolderCheck {
	requires_password: boolean;
	is_editable: boolean;
	folder_name: string;
}

export interface SharedFolderView {
	folder_name: string;
	is_editable: boolean;
	todos: SharedFolderTodo[];
}

export class SharedFolderError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
	}
}

async function readError(res: Response): Promise<string> {
	try {
		const data = await res.json();
		return data.detail || `HTTP ${res.status}`;
	} catch {
		return `HTTP ${res.status}`;
	}
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(path, {
		...init,
		credentials: 'include',
		headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) }
	});
	if (!res.ok) {
		throw new SharedFolderError(res.status, await readError(res));
	}
	if (res.status === 204) return undefined as T;
	return (await res.json()) as T;
}

export interface CreateTodoBody {
	title: string;
	description?: string | null;
	priority?: number;
	deadline?: string | null;
	parent_id?: string | null;
	sort_order?: number;
}

export interface UpdateTodoBody {
	expected_updated_at: string;
	title?: string;
	description?: string | null;
	priority?: number;
	deadline?: string | null;
	is_completed?: boolean;
	sort_order?: number;
}

export const publicFolderApi = {
	check: (pubId: string) => apiFetch<SharedFolderCheck>(`/api/pub/folder/${pubId}/check`),

	access: (pubId: string, password?: string) =>
		apiFetch<SharedFolderView>(`/api/pub/folder/${pubId}/access`, {
			method: 'POST',
			body: JSON.stringify(password ? { password } : {})
		}),

	listTodos: (pubId: string) =>
		apiFetch<SharedFolderTodo[]>(`/api/pub/folder/${pubId}/todos`),

	createTodo: (pubId: string, body: CreateTodoBody) =>
		apiFetch<SharedFolderTodo>(`/api/pub/folder/${pubId}/todos`, {
			method: 'POST',
			body: JSON.stringify(body)
		}),

	updateTodo: (pubId: string, todoId: string, body: UpdateTodoBody) =>
		apiFetch<SharedFolderTodo>(`/api/pub/folder/${pubId}/todos/${todoId}`, {
			method: 'PUT',
			body: JSON.stringify(body)
		}),

	toggleTodo: (pubId: string, todoId: string, expected_updated_at: string) =>
		apiFetch<SharedFolderTodo>(`/api/pub/folder/${pubId}/todos/${todoId}/toggle`, {
			method: 'POST',
			body: JSON.stringify({ expected_updated_at })
		}),

	deleteTodo: (pubId: string, todoId: string, expected_updated_at: string) =>
		apiFetch<void>(`/api/pub/folder/${pubId}/todos/${todoId}`, {
			method: 'DELETE',
			body: JSON.stringify({ expected_updated_at })
		}),

	reorder: (pubId: string, items: { id: string; sort_order: number }[]) =>
		apiFetch<void>(`/api/pub/folder/${pubId}/todos/reorder`, {
			method: 'PUT',
			body: JSON.stringify({ items })
		})
};
