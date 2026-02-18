/**
 * Auth API client for passkey (WebAuthn) authentication.
 * Handles registration, login, and session management via HttpOnly cookies.
 */

import {
	startRegistration,
	startAuthentication,
	browserSupportsWebAuthn
} from '@simplewebauthn/browser';
import type {
	PublicKeyCredentialCreationOptionsJSON,
	PublicKeyCredentialRequestOptionsJSON
} from '@simplewebauthn/browser';
import { PUBLIC_API_URL } from '$env/static/public';

const API_URL = PUBLIC_API_URL || 'http://localhost:8000';

export interface AuthUser {
	user_id: string;
	display_name: string;
}

interface RegisterOptionsResponse {
	options: PublicKeyCredentialCreationOptionsJSON;
	challenge_id: string;
}

interface LoginOptionsResponse {
	options: PublicKeyCredentialRequestOptionsJSON;
	challenge_id: string;
}

/**
 * Check if the browser supports WebAuthn/Passkeys.
 */
export function isPasskeySupported(): boolean {
	return browserSupportsWebAuthn();
}

/**
 * Register a new user with a passkey.
 */
export async function registerPasskey(displayName: string): Promise<AuthUser> {
	const optionsRes = await fetch(`${API_URL}/api/auth/register/options`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ display_name: displayName }),
		credentials: 'include'
	});
	if (!optionsRes.ok) {
		const error = await optionsRes.json().catch(() => ({}));
		throw new Error(error.detail || 'Failed to get registration options');
	}
	const { options, challenge_id }: RegisterOptionsResponse = await optionsRes.json();

	const credential = await startRegistration({ optionsJSON: options });

	const verifyRes = await fetch(`${API_URL}/api/auth/register/verify`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ credential, challenge_id }),
		credentials: 'include'
	});
	if (!verifyRes.ok) {
		const error = await verifyRes.json().catch(() => ({}));
		throw new Error(error.detail || 'Registration verification failed');
	}
	return verifyRes.json();
}

/**
 * Login with an existing passkey.
 */
export async function loginPasskey(): Promise<AuthUser> {
	const optionsRes = await fetch(`${API_URL}/api/auth/login/options`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		credentials: 'include'
	});
	if (!optionsRes.ok) {
		const error = await optionsRes.json().catch(() => ({}));
		throw new Error(error.detail || 'Failed to get login options');
	}
	const { options, challenge_id }: LoginOptionsResponse = await optionsRes.json();

	const credential = await startAuthentication({ optionsJSON: options });

	const verifyRes = await fetch(`${API_URL}/api/auth/login/verify`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ credential, challenge_id }),
		credentials: 'include'
	});
	if (!verifyRes.ok) {
		const error = await verifyRes.json().catch(() => ({}));
		throw new Error(error.detail || 'Login verification failed');
	}
	return verifyRes.json();
}

/**
 * Get current authenticated user from session cookie.
 */
export async function getMe(): Promise<AuthUser | null> {
	try {
		const res = await fetch(`${API_URL}/api/auth/me`, {
			credentials: 'include'
		});
		if (!res.ok) return null;
		return res.json();
	} catch {
		return null;
	}
}

/**
 * Logout and clear session cookie.
 */
export async function logout(): Promise<void> {
	await fetch(`${API_URL}/api/auth/logout`, {
		method: 'POST',
		credentials: 'include'
	});
}
