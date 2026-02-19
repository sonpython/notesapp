/**
 * Image upload service for note editor.
 * Handles validation and API calls for image uploads.
 */

import { api } from '$lib/api';
import { PUBLIC_API_URL } from '$env/static/public';
import type { ImageUploadResponse } from '$lib/types';

const API_URL = PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Convert relative API URL to absolute URL for image display.
 */
export function getAbsoluteImageUrl(relativeUrl: string): string {
	if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) {
		return relativeUrl;
	}
	return `${API_URL}${relativeUrl}`;
}

export const ALLOWED_IMAGE_TYPES = new Set([
	'image/jpeg',
	'image/png',
	'image/gif',
	'image/webp',
	'image/svg+xml'
]);

export const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

export function isAllowedImageType(file: File): boolean {
	return ALLOWED_IMAGE_TYPES.has(file.type);
}

export function isAllowedImageSize(file: File): boolean {
	return file.size <= MAX_IMAGE_SIZE;
}

export function formatFileSize(bytes: number): string {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export async function uploadNoteImage(file: File): Promise<ImageUploadResponse> {
	if (!isAllowedImageType(file)) {
		throw new Error(`Invalid file type: ${file.type}. Allowed: jpeg, png, gif, webp, svg`);
	}

	if (!isAllowedImageSize(file)) {
		throw new Error(`File too large: ${formatFileSize(file.size)}. Max: ${formatFileSize(MAX_IMAGE_SIZE)}`);
	}

	const response = await api.uploadFile<ImageUploadResponse>('/api/images/upload', file);

	// Convert relative URL to absolute URL for image display
	return {
		...response,
		url: getAbsoluteImageUrl(response.url)
	};
}
