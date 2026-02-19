/**
 * E2E encryption module for Telegram backups.
 * Uses WebAuthn PRF extension to derive AES-GCM keys from passkeys.
 */

import { startAuthentication } from '@simplewebauthn/browser';
import type { PublicKeyCredentialRequestOptionsJSON } from '@simplewebauthn/browser';
const API_URL = '';

// Fixed PRF salt for backup encryption (32 bytes, base64url encoded)
// This is application-specific and safe to be public
const PRF_SALT = new Uint8Array([
	0x4e, 0x6f, 0x74, 0x65, 0x73, 0x41, 0x70, 0x70, // "NotesApp"
	0x42, 0x61, 0x63, 0x6b, 0x75, 0x70, 0x45, 0x6e, // "BackupEn"
	0x63, 0x72, 0x79, 0x70, 0x74, 0x69, 0x6f, 0x6e, // "cryption"
	0x4b, 0x65, 0x79, 0x56, 0x31, 0x00, 0x00, 0x00 // "KeyV1..."
]);

/**
 * Check if browser supports WebAuthn PRF extension.
 * PRF is supported in Chrome 116+, Safari 17+, Edge 116+.
 * Firefox does not support PRF yet.
 */
export async function isPrfSupported(): Promise<boolean> {
	if (typeof window === 'undefined' || !window.PublicKeyCredential) return false;

	const ua = navigator.userAgent;

	// Firefox doesn't support PRF
	if (/Firefox/i.test(ua)) return false;

	// Chrome/Edge 116+ support PRF
	const chromeMatch = /Chrom(?:e|ium)\/(\d+)/i.exec(ua);
	if (chromeMatch) {
		return parseInt(chromeMatch[1], 10) >= 116;
	}

	// Safari 17+ supports PRF (check Version/ for actual Safari version)
	if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) {
		const versionMatch = /Version\/(\d+)/i.exec(ua);
		if (versionMatch) {
			return parseInt(versionMatch[1], 10) >= 17;
		}
	}

	return false;
}

/**
 * Result from PRF key derivation.
 */
export interface PrfKeyResult {
	key: CryptoKey;
	credentialId: string;
}

/**
 * Derive an AES-GCM key from passkey using WebAuthn PRF extension.
 * Triggers a passkey authentication ceremony with PRF extension.
 *
 * @returns AES-GCM CryptoKey derived from PRF output
 * @throws Error if PRF not supported or authentication fails
 */
export async function deriveKeyFromPasskey(): Promise<PrfKeyResult> {
	// Check PRF support first
	const supported = await isPrfSupported();
	if (!supported) {
		throw new Error(
			'Your browser does not support encrypted backups. ' +
				'Please use Chrome 116+, Safari 17+, or Edge 116+.'
		);
	}

	// Get authentication options from backend
	const optionsRes = await fetch(`${API_URL}/api/auth/login/options`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		credentials: 'include'
	});

	if (!optionsRes.ok) {
		throw new Error('Failed to get authentication options');
	}

	const { options, challenge_id } = (await optionsRes.json()) as {
		options: PublicKeyCredentialRequestOptionsJSON;
		challenge_id: string;
	};

	// Add PRF extension to the options (first must be ArrayBuffer)
	const prfOptions = {
		...options,
		extensions: {
			...options.extensions,
			prf: {
				eval: {
					first: PRF_SALT.buffer
				}
			}
		}
	};

	// Start authentication with PRF
	const credential = await startAuthentication({
		optionsJSON: prfOptions as PublicKeyCredentialRequestOptionsJSON
	});

	// Verify authentication (maintain session)
	const verifyRes = await fetch(`${API_URL}/api/auth/login/verify`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ credential, challenge_id }),
		credentials: 'include'
	});

	if (!verifyRes.ok) {
		throw new Error('Passkey verification failed');
	}

	// Extract PRF result from client extension results
	// @ts-expect-error - PRF extension types not fully defined
	const prfResult = credential.clientExtensionResults?.prf?.results?.first as ArrayBuffer | undefined;

	if (!prfResult) {
		throw new Error(
			'PRF extension not available. Your passkey may not support encrypted backups.'
		);
	}

	// PRF output is ArrayBuffer, convert to Uint8Array
	const prfOutput = new Uint8Array(prfResult);

	// Derive AES-GCM key from PRF output using HKDF
	const keyMaterial = await crypto.subtle.importKey(
		'raw',
		prfOutput.buffer as ArrayBuffer,
		'HKDF',
		false,
		['deriveKey']
	);

	const aesKey = await crypto.subtle.deriveKey(
		{
			name: 'HKDF',
			salt: PRF_SALT,
			info: new TextEncoder().encode('NotesApp Backup Encryption'),
			hash: 'SHA-256'
		},
		keyMaterial,
		{ name: 'AES-GCM', length: 256 },
		false,
		['encrypt', 'decrypt']
	);

	return {
		key: aesKey,
		credentialId: credential.id
	};
}

/**
 * Encrypt data using AES-GCM.
 *
 * @param key AES-GCM CryptoKey
 * @param data String data to encrypt
 * @returns Base64-encoded ciphertext and IV
 */
export async function encryptData(
	key: CryptoKey,
	data: string
): Promise<{ ciphertext: string; iv: string }> {
	// Generate random 12-byte IV (recommended for AES-GCM)
	const iv = crypto.getRandomValues(new Uint8Array(12));

	// Encode data as UTF-8
	const plaintext = new TextEncoder().encode(data);

	// Encrypt
	const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, plaintext);

	return {
		ciphertext: bufferToBase64(new Uint8Array(ciphertext)),
		iv: bufferToBase64(iv)
	};
}

/**
 * Decrypt data using AES-GCM.
 *
 * @param key AES-GCM CryptoKey
 * @param ciphertext Base64-encoded ciphertext
 * @param iv Base64-encoded IV
 * @returns Decrypted string
 */
export async function decryptData(key: CryptoKey, ciphertext: string, iv: string): Promise<string> {
	const ciphertextBuffer = base64ToBuffer(ciphertext);
	const ivBuffer = base64ToBuffer(iv);

	const plaintext = await crypto.subtle.decrypt(
		{ name: 'AES-GCM', iv: ivBuffer.buffer as ArrayBuffer },
		key,
		ciphertextBuffer.buffer as ArrayBuffer
	);

	return new TextDecoder().decode(plaintext);
}

/**
 * Derive AES-GCM key from password using PBKDF2.
 * Fallback when PRF not supported.
 */
export async function deriveKeyFromPassword(password: string): Promise<CryptoKey> {
	const encoder = new TextEncoder();
	const passwordBuffer = encoder.encode(password);

	// Import password as key material
	const keyMaterial = await crypto.subtle.importKey('raw', passwordBuffer, 'PBKDF2', false, [
		'deriveKey'
	]);

	// Derive AES-256-GCM key with PBKDF2
	return crypto.subtle.deriveKey(
		{
			name: 'PBKDF2',
			salt: PRF_SALT,
			iterations: 100000,
			hash: 'SHA-256'
		},
		keyMaterial,
		{ name: 'AES-GCM', length: 256 },
		false,
		['encrypt', 'decrypt']
	);
}

// --- Utility functions ---

function bufferToBase64(buffer: Uint8Array): string {
	return btoa(String.fromCharCode(...buffer));
}

function base64ToBuffer(base64: string): Uint8Array {
	const binary = atob(base64);
	const bytes = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i++) {
		bytes[i] = binary.charCodeAt(i);
	}
	return bytes;
}

function bufferToBase64url(buffer: Uint8Array): string {
	return bufferToBase64(buffer).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64urlToBuffer(base64url: string): Uint8Array {
	const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
	const paddedBase64 = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
	return base64ToBuffer(paddedBase64);
}
