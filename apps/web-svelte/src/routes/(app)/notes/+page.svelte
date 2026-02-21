<script lang="ts">
	/**
	 * Notes page - responsive layout.
	 * Mobile: full-screen list OR editor (swipe between).
	 * Desktop: two-pane layout.
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { NotesStore } from '$lib/stores/notes-store.svelte';
	import { tagsStore } from '$lib/stores/tags-store.svelte';
	import { createDebounced } from '$lib/utils/debounce.svelte';
	import NoteList from '$lib/components/notes/note-list.svelte';
	import NoteEditor from '$lib/components/notes/note-editor.svelte';
	import { Plus, Search, ChevronLeft } from 'lucide-svelte';
	import type { Note, Tag } from '$lib/types';

	const notesStore = new NotesStore();
	

	let selectedNoteId = $state<string | null>(null);
	let mobileShowEditor = $state(false); // Mobile: show editor instead of list
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
		mobileShowEditor = true;
	}

	function handleSelectNote(id: string) {
		selectedNoteId = id;
		mobileShowEditor = true;
	}

	function handleBackToList() {
		mobileShowEditor = false;
	}

	function handleSaveNote(
		id: string,
		data: { title?: string; content?: string; is_pinned?: boolean; is_archived?: boolean }
	) {
		notesStore.updateNote(id, data as Partial<Note>);
	}

	async function handleDeleteNote(id: string) {
		await notesStore.deleteNote(id);
		if (selectedNoteId === id) {
			selectedNoteId = null;
			mobileShowEditor = false;
		}
	}

	function handleTagsChange(noteId: string, tags: Tag[]) {
		notesStore.updateNoteTags(noteId, tags);
	}

	async function handleMoveNote(noteId: string, targetFolderId: string | null) {
		await notesStore.moveNoteToFolder(noteId, targetFolderId);
	}
</script>

<svelte:head>
	<title>Notes - NotesApp</title>
</svelte:head>

<!-- Mobile: full-screen views -->
<div class="flex h-full w-full overflow-hidden lg:hidden">
	{#if mobileShowEditor && selectedNote}
		<!-- Mobile: Editor view -->
		<div class="flex h-full w-full flex-col">
			<!-- Mobile editor header -->
			<div class="flex h-12 shrink-0 items-center gap-2 border-b border-border bg-background px-2">
				<button
					onclick={handleBackToList}
					class="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm text-accent hover:bg-sidebar"
				>
					<ChevronLeft class="h-4 w-4" />
					<span>Notes</span>
				</button>
			</div>
			<div class="flex-1 overflow-hidden">
				<NoteEditor
					note={selectedNote}
					onsave={handleSaveNote}
					ondelete={handleDeleteNote}
					ontagschange={handleTagsChange}
				/>
			</div>
		</div>
	{:else}
		<!-- Mobile: List view -->
		<div class="flex h-full w-full flex-col bg-sidebar">
			<NoteList
				notes={notesStore.notes}
				selectedId={selectedNoteId}
				onselect={handleSelectNote}
				onmoveNote={handleMoveNote}
				onLoadMore={() => notesStore.loadMore()}
				hasMore={notesStore.hasMore}
				loading={notesStore.loading}
			/>
		</div>
		<!-- FAB: Create note -->
		<button
			onclick={handleCreateNote}
			class="fixed bottom-20 right-4 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-accent text-black shadow-lg transition-transform hover:scale-105 active:scale-95"
			aria-label="New note"
		>
			<Plus class="h-6 w-6" />
		</button>
	{/if}
</div>

<!-- Desktop: Two-pane layout -->
<div class="hidden h-full w-full overflow-hidden lg:flex">
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
				onLoadMore={() => notesStore.loadMore()}
				hasMore={notesStore.hasMore}
				loading={notesStore.loading}
			/>
		</div>
	</div>

	<!-- Right pane: editor -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<NoteEditor
			note={selectedNote}
			onsave={handleSaveNote}
			ondelete={handleDeleteNote}
			ontagschange={handleTagsChange}
		/>
	</div>
</div>
