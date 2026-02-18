/**
 * CodeMirror extension for drag-and-drop and paste image support.
 * Inserts markdown image syntax after uploading to backend.
 */

import { EditorView } from '@codemirror/view';
import { isAllowedImageType, isAllowedImageSize, formatFileSize, MAX_IMAGE_SIZE } from '$lib/services/image-upload-service';

export interface ImageUploadResult {
	url: string;
}

type UploadHandler = (file: File) => Promise<ImageUploadResult>;
type ErrorHandler = (message: string) => void;

/**
 * Extract image files from DataTransfer (drop or paste event).
 */
function getImageFiles(dataTransfer: DataTransfer | null): File[] {
	if (!dataTransfer) return [];
	const files: File[] = [];
	for (const item of dataTransfer.items) {
		if (item.kind === 'file' && item.type.startsWith('image/')) {
			const file = item.getAsFile();
			if (file) files.push(file);
		}
	}
	return files;
}

/**
 * Insert text at the current cursor position or replace selection.
 */
function insertText(view: EditorView, text: string, from?: number, to?: number): void {
	const pos = from ?? view.state.selection.main.head;
	const endPos = to ?? pos;
	view.dispatch({
		changes: { from: pos, to: endPos, insert: text },
		selection: { anchor: pos + text.length }
	});
}

/**
 * Find and replace placeholder text in the document.
 */
function replacePlaceholder(view: EditorView, placeholder: string, replacement: string): void {
	const doc = view.state.doc.toString();
	const index = doc.indexOf(placeholder);
	if (index !== -1) {
		view.dispatch({
			changes: { from: index, to: index + placeholder.length, insert: replacement }
		});
	}
}

/**
 * Handle a single image upload with placeholder.
 */
async function handleImageUpload(
	view: EditorView,
	file: File,
	onUpload: UploadHandler,
	onError?: ErrorHandler
): Promise<void> {
	// Validate file type
	if (!isAllowedImageType(file)) {
		onError?.(`Invalid file type: ${file.type}`);
		return;
	}

	// Validate file size
	if (!isAllowedImageSize(file)) {
		onError?.(`File too large: ${formatFileSize(file.size)}. Max: ${formatFileSize(MAX_IMAGE_SIZE)}`);
		return;
	}

	// Create unique placeholder
	const placeholderId = Math.random().toString(36).substring(2, 8);
	const placeholder = `![Uploading ${file.name}...](placeholder-${placeholderId})`;

	// Insert placeholder at cursor
	insertText(view, placeholder);

	try {
		const result = await onUpload(file);
		const markdown = `![${file.name}](${result.url})`;
		replacePlaceholder(view, placeholder, markdown);
	} catch (err) {
		const errorMessage = err instanceof Error ? err.message : 'Upload failed';
		replacePlaceholder(view, placeholder, `![Upload failed: ${errorMessage}]()`);
		onError?.(errorMessage);
	}
}

/**
 * Create CodeMirror extension for image drag-and-drop and paste.
 */
export function imageDropExtension(
	onUpload: UploadHandler,
	onError?: ErrorHandler
) {
	return EditorView.domEventHandlers({
		drop(event, view) {
			const files = getImageFiles(event.dataTransfer);
			if (files.length === 0) return false;

			event.preventDefault();
			event.stopPropagation();

			// Get drop position
			const pos = view.posAtCoords({ x: event.clientX, y: event.clientY });
			if (pos !== null) {
				view.dispatch({ selection: { anchor: pos } });
			}

			// Upload all dropped images
			for (const file of files) {
				handleImageUpload(view, file, onUpload, onError);
			}

			return true;
		},

		paste(event, view) {
			const files = getImageFiles(event.clipboardData);
			if (files.length === 0) return false;

			event.preventDefault();
			event.stopPropagation();

			// Upload all pasted images
			for (const file of files) {
				handleImageUpload(view, file, onUpload, onError);
			}

			return true;
		}
	});
}
