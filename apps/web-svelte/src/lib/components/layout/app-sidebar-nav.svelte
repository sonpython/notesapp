<script lang="ts">
	/**
	 * Sidebar navigation section: nav links, folder tree, and tag filters.
	 * Split from app-sidebar to keep file size under 200 lines.
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { CheckSquare, Settings, Tag as TagIcon } from 'lucide-svelte';
	import type { FoldersStore } from '$lib/stores/folders-store.svelte';
	import type { TagsStore } from '$lib/stores/tags-store.svelte';
	import type { NotesStore } from '$lib/stores/notes-store.svelte';
	import FolderTree from '$lib/components/folders/folder-tree.svelte';

	interface Props {
		foldersStore: FoldersStore;
		tagsStore: TagsStore;
		notesStore: NotesStore;
		onnavigate?: () => void;
	}

	let { foldersStore, tagsStore, notesStore, onnavigate }: Props = $props();

	let isCreatingFolder = $state(false);

	const navItems = [
		{ label: 'Todos', href: '/todos?filter=active', icon: CheckSquare },
		{ label: 'Settings', href: '/settings', icon: Settings },
	] as const;

	const pathname = $derived($page.url.pathname);
	const searchParams = $derived($page.url.searchParams);
	const selectedFolderId = $derived(searchParams.get('folder'));
	const selectedTagIds = $derived(
		searchParams.get('tags') ? searchParams.get('tags')!.split(',') : []
	);

	// Fetch note counts on mount and subscribe to changes from other store instances
	$effect(() => {
		notesStore.fetchNoteCounts();
		const unsubscribe = notesStore.subscribeToChanges();
		return unsubscribe;
	});

	function selectFolder(id: string | null) {
		goto(id ? `/notes?folder=${id}` : '/notes');
		onnavigate?.();
	}

	async function createFolder(name: string, parentId?: string) {
		return await foldersStore.createFolder(name, parentId);
	}

	async function renameFolder(id: string, name: string) {
		return await foldersStore.updateFolder(id, { name });
	}

	async function deleteFolder(id: string) {
		await foldersStore.deleteFolder(id);
		if (selectedFolderId === id) goto('/notes');
	}

	async function moveNote(noteId: string, folderId: string | null) {
		await notesStore.moveNoteToFolder(noteId, folderId);
	}

	function toggleTag(tagId: string) {
		const next = selectedTagIds.includes(tagId)
			? selectedTagIds.filter((id) => id !== tagId)
			: [...selectedTagIds, tagId];

		const params = new URLSearchParams(searchParams.toString());
		if (next.length > 0) {
			params.set('tags', next.join(','));
		} else {
			params.delete('tags');
		}
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

<!-- Folder tree with "All Notes" -->
<div class="flex-1 overflow-y-auto px-3">
	<FolderTree
		folders={foldersStore.folderTree}
		{selectedFolderId}
		noteCounts={notesStore.counts}
		onselectFolder={selectFolder}
		oncreateFolder={createFolder}
		onrenameFolder={renameFolder}
		ondeleteFolder={deleteFolder}
		onmoveNote={moveNote}
	/>
</div>

<div class="mx-5 my-3 border-t border-border"></div>

<!-- Other navigation links -->
<nav class="space-y-0.5 px-3">
	{#each navItems as item (item.href)}
		{@const isActive = pathname.startsWith(item.href)}
		<a
			href={item.href}
			onclick={onnavigate}
			class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive
				? 'bg-accent/15 text-accent'
				: 'text-muted hover:bg-border hover:text-foreground'}"
		>
			<item.icon class="h-4 w-4 shrink-0" />
			{item.label}
		</a>
	{/each}
</nav>

<div class="mx-5 my-3 border-t border-border"></div>

<!-- Tags section header -->
<div class="flex items-center justify-between px-5 pb-2">
	<span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Tags</span>
	<a
		href="/settings?tab=tags"
		onclick={onnavigate}
		class="rounded p-1 text-zinc-500 transition-colors hover:bg-border hover:text-zinc-300"
		title="Manage Tags"
	>
		<TagIcon class="h-3.5 w-3.5" />
	</a>
</div>

<!-- Tag filter list -->
<div class="px-3 pb-3">
	<!--
		TODO: Replace with <TagFilterSection> component once migrated.
		Props: tags={tagsStore.tags} {selectedTagIds} onToggleTag={toggleTag} onClearAll={clearTagFilters}
	-->
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
			<button
				type="button"
				onclick={clearTagFilters}
				class="mt-1 text-xs text-zinc-500 hover:text-zinc-300"
			>
				Clear filters
			</button>
		{/if}
	{/if}
</div>
