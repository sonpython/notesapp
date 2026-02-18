/**
 * Image upload service for note editor.
 * Handles validation and API calls for image uploads.
 */

import { api } from '$lib/api';
import type { ImageUploadResponse } from '$lib/types';

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

	return api.uploadFile<ImageUploadResponse>('/api/images/upload', file);
}
