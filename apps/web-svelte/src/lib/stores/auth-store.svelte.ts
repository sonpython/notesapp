/**
 * Auth store - singleton for authentication state.
 * Uses HttpOnly session cookie - no client-side token handling.
 */

import { getMe, logout as logoutApi, type AuthUser } from '$lib/auth-api';

class AuthStore {
	user = $state<AuthUser | null>(null);
	loading = $state(true);

	async init() {
		try {
			this.user = await getMe();
		} catch {
			this.user = null;
		} finally {
			this.loading = false;
		}
	}

	async signOut() {
		try {
			await logoutApi();
		} catch {
			// Ignore logout errors - clear local state anyway
		}
		this.user = null;
	}
}

export const authStore = new AuthStore();
