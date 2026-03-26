<script lang="ts">
	/**
	 * Sidebar navigation: accordion sections for Notes and Todos,
	 * each with folder trees. Only one section expanded at a time.
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { FileText, CheckSquare, ChevronDown, ChevronRight, Settings, Tag as TagIcon } from 'lucide-svelte';
	import type { FoldersStore } from '$lib/stores/folders-store.svelte';
	import type { TagsStore } from '$lib/stores/tags-store.svelte';
	import type { NotesStore } from '$lib/stores/notes-store.svelte';
	import type { TodosStore } from '$lib/stores/todos-store.svelte';
	import type { TodoFoldersStore } from '$lib/stores/todo-folders-store.svelte';
	import FolderTree from '$lib/components/folders/folder-tree.svelte';
	import TodoFolderTree from '$lib/components/todo-folders/todo-folder-tree.svelte';

	interface Props {
		foldersStore: FoldersStore;
		tagsStore: TagsStore;
		notesStore: NotesStore;
		todosStore: TodosStore;
		todoFoldersStore: TodoFoldersStore;
		onnavigate?: () => void;
	}

	let { foldersStore, tagsStore, notesStore, todosStore, todoFoldersStore, onnavigate }: Props = $props();

	const pathname = $derived($page.url.pathname);
	const searchParams = $derived($page.url.searchParams);
	const selectedNoteFolderId = $derived(searchParams.get('folder'));
	const selectedTodoFolderId = $derived(searchParams.get('folder'));
	const selectedTagIds = $derived(
		searchParams.get('tags') ? searchParams.get('tags')!.split(',') : []
	);

	// Accordion: auto-expand based on current route
	type Section = 'notes' | 'todos';
	let expandedSection = $state<Section>(pathname.startsWith('/todos') ? 'todos' : 'notes');

	// Track route changes to auto-switch section
	$effect(() => {
		if (pathname.startsWith('/todos')) expandedSection = 'todos';
		else if (pathname.startsWith('/notes')) expandedSection = 'notes';
	});

	// Fetch note counts
	$effect(() => {
		notesStore.fetchNoteCounts();
		const unsubscribe = notesStore.subscribeToChanges();
		return unsubscribe;
	});

	function toggleSection(section: Section) {
		expandedSection = section;
		if (section === 'notes') goto('/notes');
		else goto('/todos?filter=active');
		onnavigate?.();
	}

	// Note folder handlers
	function selectNoteFolder(id: string | null, name?: string) {
		if (id && name) goto(`/notes?folder=${id}&fn=${encodeURIComponent(name)}`);
		else goto('/notes');
		onnavigate?.();
	}

	async function createNoteFolder(name: string, parentId?: string) {
		return await foldersStore.createFolder(name, parentId);
	}
	async function renameNoteFolder(id: string, name: string) {
		return await foldersStore.updateFolder(id, { name });
	}
	async function deleteNoteFolder(id: string, cascade: boolean) {
		await foldersStore.deleteFolder(id, cascade);
		if (selectedNoteFolderId === id) goto('/notes');
	}
	async function moveNote(noteId: string, folderId: string | null) {
		await notesStore.moveNoteToFolder(noteId, folderId);
	}

	// Todo folder handlers
	function selectTodoFolder(id: string | null) {
		if (id) goto(`/todos?folder=${id}&filter=active`);
		else goto('/todos?filter=active');
		onnavigate?.();
	}

	async function createTodoFolder(name: string, parentId?: string) {
		return await todoFoldersStore.createFolder(name, parentId);
	}
	async function renameTodoFolder(id: string, name: string) {
		return await todoFoldersStore.updateFolder(id, { name });
	}
	async function deleteTodoFolder(id: string, cascade: boolean) {
		await todoFoldersStore.deleteFolder(id, cascade);
		if (selectedTodoFolderId === id) goto('/todos?filter=active');
	}

	// Tag handlers
	function toggleTag(tagId: string) {
		const next = selectedTagIds.includes(tagId)
			? selectedTagIds.filter((id) => id !== tagId)
			: [...selectedTagIds, tagId];
		const params = new URLSearchParams(searchParams.toString());
		if (next.length > 0) params.set('tags', next.join(','));
		else params.delete('tags');
		goto(`${pathname}?${params.toString()}`);
		onnavigate?.();
	}

	function clearTagFilters() {
		const params = new URLSearchParams(searchParams.toString());
		params.delete('tags');
		goto(`${pathname}?${params.toString()}`);
		onnavigate?.();
	}
</script>

<div class="flex-1 overflow-y-auto px-3">
	<!-- Notes section -->
	<button
		type="button"
		onclick={() => toggleSection('notes')}
		class="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors
			{expandedSection === 'notes' ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'}"
	>
		{#if expandedSection === 'notes'}
			<ChevronDown class="h-3.5 w-3.5 shrink-0" />
		{:else}
			<ChevronRight class="h-3.5 w-3.5 shrink-0" />
		{/if}
		<FileText class="h-4 w-4 shrink-0" />
		<span class="flex-1 text-left">Notes</span>
		{#if notesStore.counts?.total}
			<span class="text-xs text-zinc-500">{notesStore.counts.total}</span>
		{/if}
	</button>

	{#if expandedSection === 'notes'}
		<div class="ml-2">
			<FolderTree
				folders={foldersStore.folderTree}
				selectedFolderId={pathname.startsWith('/notes') ? selectedNoteFolderId : null}
				noteCounts={notesStore.counts}
				onselectFolder={selectNoteFolder}
				oncreateFolder={createNoteFolder}
				onrenameFolder={renameNoteFolder}
				ondeleteFolder={deleteNoteFolder}
				onmoveNote={moveNote}
			/>
		</div>
	{/if}

	<div class="my-1"></div>

	<!-- Todos section -->
	<button
		type="button"
		onclick={() => toggleSection('todos')}
		class="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors
			{expandedSection === 'todos' ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'}"
	>
		{#if expandedSection === 'todos'}
			<ChevronDown class="h-3.5 w-3.5 shrink-0" />
		{:else}
			<ChevronRight class="h-3.5 w-3.5 shrink-0" />
		{/if}
		<CheckSquare class="h-4 w-4 shrink-0" />
		<span class="flex-1 text-left">Todos</span>
		{#if todosStore.counts.total > 0}
			<span class="text-xs text-zinc-500">
				{todosStore.counts.active}/{todosStore.counts.total}
			</span>
		{/if}
	</button>

	{#if expandedSection === 'todos'}
		<div class="ml-2">
			<TodoFolderTree
				folders={todoFoldersStore.folderTree}
				selectedFolderId={pathname.startsWith('/todos') ? selectedTodoFolderId : null}
				onselectFolder={selectTodoFolder}
				oncreateFolder={createTodoFolder}
				onrenameFolder={renameTodoFolder}
				ondeleteFolder={deleteTodoFolder}
			/>
		</div>
	{/if}
</div>

<div class="mx-5 my-3 border-t border-border"></div>

<!-- Settings link -->
<nav class="space-y-0.5 px-3">
	<a
		href="/settings"
		onclick={onnavigate}
		class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {pathname.startsWith('/settings')
			? 'bg-accent/15 text-accent'
			: 'text-muted hover:bg-border hover:text-foreground'}"
	>
		<Settings class="h-4 w-4 shrink-0" />
		Settings
	</a>
</nav>

<div class="mx-5 my-3 border-t border-border"></div>

<!-- Tags section -->
<div class="flex items-center justify-between px-5 pb-2">
	<span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Tags</span>
	<a href="/settings?tab=tags" onclick={onnavigate}
		class="rounded p-1 text-zinc-500 transition-colors hover:bg-border hover:text-zinc-300" title="Manage Tags">
		<TagIcon class="h-3.5 w-3.5" />
	</a>
</div>

<div class="px-3 pb-3">
	{#if tagsStore.tags?.length > 0}
		<div class="flex flex-wrap gap-1">
			{#each tagsStore.tags as tag (tag.id)}
				<button
					type="button"
					onclick={() => toggleTag(tag.id)}
					class="rounded-full px-2 py-0.5 text-xs transition-colors {selectedTagIds.includes(tag.id)
						? 'bg-zinc-600 text-white'
						: 'bg-zinc-800 text-muted hover:bg-zinc-700 hover:text-foreground'}"
					style={tag.color ? `border: 1px solid ${tag.color}` : ''}
				>
					{tag.name}
				</button>
			{/each}
		</div>
		{#if selectedTagIds?.length > 0}
			<button type="button" onclick={clearTagFilters} class="mt-1 text-xs text-zinc-500 hover:text-zinc-300">
				Clear filters
			</button>
		{/if}
	{/if}
</div>
