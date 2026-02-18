<script lang="ts">
	/**
	 * App sidebar shell - user controls + composes AppSidebarNav.
	 * Apple Notes-inspired dark sidebar (zinc-900).
	 */
	import { goto } from '$app/navigation';
	import { LogOut } from 'lucide-svelte';
	import { authStore } from '$lib/stores/auth-store.svelte';
	import { FoldersStore } from '$lib/stores/folders-store.svelte';
	import { NotesStore } from '$lib/stores/notes-store.svelte';
	import { TagsStore } from '$lib/stores/tags-store.svelte';
	import ThemeToggleButton from '$lib/components/ui/theme-toggle-button.svelte';
	import AppSidebarNav from './app-sidebar-nav.svelte';

	// Instantiate stores as singletons for this sidebar session
	const foldersStore = new FoldersStore();
	const notesStore = new NotesStore();
	const tagsStore = new TagsStore();

	// Fetch data on mount
	$effect(() => {
		foldersStore.fetchFolders();
		tagsStore.fetchTags();
	});

	async function handleSignOut() {
		await authStore.signOut();
		goto('/login');
	}
</script>

<aside class="flex h-full w-64 flex-col bg-zinc-900 text-zinc-300">
	<!-- App title -->
	<div class="flex h-14 items-center px-5">
		<h1 class="text-lg font-semibold tracking-tight text-white">NotesApp</h1>
	</div>

	<!-- Nav, folders, tags -->
	<AppSidebarNav {foldersStore} {tagsStore} />

	<!-- User section at bottom -->
	<div class="border-t border-zinc-800 px-4 py-3">
		<div class="flex items-center justify-between gap-2">
			<span class="truncate text-xs text-zinc-500">
				{authStore.user?.display_name ?? 'Loading...'}
			</span>
			<div class="flex shrink-0 items-center gap-1">
				<ThemeToggleButton />
				<button
					type="button"
					onclick={handleSignOut}
					class="rounded p-1.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
					title="Sign out"
				>
					<LogOut class="h-3.5 w-3.5" />
				</button>
			</div>
		</div>
	</div>
</aside>
