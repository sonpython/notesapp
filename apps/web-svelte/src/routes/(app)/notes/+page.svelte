<script lang="ts">
	/**
	 * Notes page - two-pane layout: note list + editor.
	 * URL params: folder, tags (comma-separated IDs), search.
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { NotesStore } from '$lib/stores/notes-store.svelte';
	import { TagsStore } from '$lib/stores/tags-store.svelte';
	import { createDebounced } from '$lib/utils/debounce.svelte';
	import NoteList from '$lib/components/notes/note-list.svelte';
	import NoteEditor from '$lib/components/notes/note-editor.svelte';
	import { Plus, Search } from 'lucide-svelte';
	import type { Note } from '$lib/types';

	const notesStore = new NotesStore();
	const tagsStore = new TagsStore();

	let selectedNoteId = $state<string | null>(null);
	const searchInput = createDebounced('', 400);

	// Derive URL params reactively
	const folderId = $derived($page.url.searchParams.get('folder') ?? undefined);
	const tagParam = $derived($page.url.searchParams.get('tags') ?? '');
	const tagIds = $derived(tagParam ? tagParam.split(',').filter(Boolean) : undefined);
	const urlSearch = $derived($page.url.searchParams.get('search') ?? '');

	// Sync search input from URL on navigation
	$effect(() => {
		searchInput.setImmediate(urlSearch);
	});

	// Fetch notes when URL params or debounced search changes
	$effect(() => {
		const search = searchInput.debounced || undefined;
		notesStore.fetchNotes(folderId, search, tagIds);
	});

	onMount(() => {
		tagsStore.fetchTags();
	});

	const selectedNote = $derived(
		selectedNoteId ? (notesStore.notes.find((n) => n.id === selectedNoteId) ?? null) : null
	);

	function handleSearchChange(e: Event) {
		const value = (e.target as HTMLInputElement).value;
		searchInput.set(value);
		// Reflect search in URL
		const params = new URLSearchParams($page.url.searchParams);
		if (value) {
			params.set('search', value);
		} else {
			params.delete('search');
		}
		goto(`?${params.toString()}`, { replaceState: true, keepFocus: true });
	}

	async function handleCreateNote() {
		const note = await notesStore.createNote({
			title: '',
			content: '',
			folder_id: folderId ?? null
		});
		selectedNoteId = note.id;
	}

	function handleSaveNote(
		id: string,
		data: { title?: string; content?: string; is_pinned?: boolean; is_archived?: boolean }
	) {
		notesStore.updateNote(id, data as Partial<Note>);
	}

	async function handleDeleteNote(id: string) {
		await notesStore.deleteNote(id);
		if (selectedNoteId === id) selectedNoteId = null;
	}

	async function handleMoveNote(noteId: string, targetFolderId: string | null) {
		await notesStore.moveNoteToFolder(noteId, targetFolderId);
	}
</script>

<svelte:head>
	<title>Notes - NotesApp</title>
</svelte:head>

<!-- Two-pane layout: list (fixed width) + editor (flex-1) -->
<div class="flex h-full w-full overflow-hidden">
	<!-- Left pane: search + list -->
	<div class="flex w-64 shrink-0 flex-col border-r border-border bg-sidebar xl:w-72">
		<!-- Search + new note toolbar -->
		<div class="flex items-center gap-1.5 border-b border-border px-3 py-2">
			<div class="relative flex-1">
				<Search class="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
				<input
					type="search"
					value={searchInput.value}
					oninput={handleSearchChange}
					placeholder="Search notes..."
					class="h-7 w-full rounded-md border border-border bg-background pl-7 pr-2 text-xs text-foreground placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
				/>
			</div>
			<button
				onclick={handleCreateNote}
				title="New note"
				class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent text-black transition-opacity hover:opacity-90"
			>
				<Plus class="h-4 w-4" />
			</button>
		</div>

		<!-- Note list -->
		<div class="flex-1 overflow-hidden">
			<NoteList
				notes={notesStore.notes}
				selectedId={selectedNoteId}
				onselect={(id) => (selectedNoteId = id)}
				onmoveNote={handleMoveNote}
			/>
		</div>
	</div>

	<!-- Right pane: editor -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<NoteEditor
			note={selectedNote}
			onsave={handleSaveNote}
			ondelete={handleDeleteNote}
		/>
	</div>
</div>
