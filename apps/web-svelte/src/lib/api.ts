/**
 * API client for the NotesApp backend.
 * Uses HttpOnly session cookie for authentication (set by passkey login).
 * Uses relative URLs - works for both dev (with proxy) and prod (same domain).
 */

const API_URL = '';

class ApiClient {
	private async request<T>(path: string, init?: RequestInit): Promise<T> {
		const res = await fetch(`${API_URL}${path}`, {
			...init,
			headers: {
				'Content-Type': 'application/json',
				...init?.headers
			},
			credentials: 'include' // Send session cookie automatically
		});
		if (!res.ok) throw new Error(`API error: ${res.status}`);
		return res.json();
	}

	async get<T>(path: string): Promise<T> {
		return this.request<T>(path);
	}

	async post<T>(path: string, body?: unknown): Promise<T> {
		return this.request<T>(path, {
			method: 'POST',
			body: body ? JSON.stringify(body) : undefined
		});
	}

	async put<T>(path: string, body: unknown): Promise<T> {
		return this.request<T>(path, {
			method: 'PUT',
			body: JSON.stringify(body)
		});
	}

	async delete(path: string): Promise<void> {
		const res = await fetch(`${API_URL}${path}`, {
			method: 'DELETE',
			credentials: 'include'
		});
		if (!res.ok) throw new Error(`API error: ${res.status}`);
	}

	async uploadFile<T>(path: string, file: File): Promise<T> {
		const formData = new FormData();
		formData.append('file', file);
		const res = await fetch(`${API_URL}${path}`, {
			method: 'POST',
			body: formData,
			credentials: 'include'
			// No Content-Type header -- browser sets multipart boundary
		});
		if (!res.ok) {
			const error = await res.text();
			throw new Error(`Upload failed: ${res.status} - ${error}`);
		}
		return res.json();
	}
}

export const api = new ApiClient();
