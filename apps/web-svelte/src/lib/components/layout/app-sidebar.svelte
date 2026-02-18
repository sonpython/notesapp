<script lang="ts">
	/**
	 * App sidebar shell - user controls + composes AppSidebarNav.
	 * Apple Notes-inspired dark sidebar (zinc-900).
	 */
	import { goto } from '$app/navigation';
	import { LogOut, PanelLeftClose, FileText, CheckSquare, Settings } from 'lucide-svelte';
	import { authStore } from '$lib/stores/auth-store.svelte';
	import { FoldersStore } from '$lib/stores/folders-store.svelte';
	import { NotesStore } from '$lib/stores/notes-store.svelte';
	import { TagsStore } from '$lib/stores/tags-store.svelte';
	import ThemeToggleButton from '$lib/components/ui/theme-toggle-button.svelte';
	import AppSidebarNav from './app-sidebar-nav.svelte';

	interface Props {
		oncollapse?: () => void;
		collapsed?: boolean;
	}
	let { oncollapse, collapsed = false }: Props = $props();

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

<aside class="flex h-full w-full flex-col bg-zinc-900 text-zinc-300">
	{#if collapsed}
		<!-- Collapsed: icons only -->
		<div class="flex flex-col items-center py-3 gap-2">
			<button onclick={oncollapse} class="p-2 text-zinc-400 hover:text-white" title="Expand">
				<PanelLeftClose class="h-5 w-5 rotate-180" />
			</button>
			<a href="/notes" class="p-2 text-zinc-400 hover:text-white" title="Notes">
				<FileText class="h-5 w-5" />
			</a>
			<a href="/todos" class="p-2 text-zinc-400 hover:text-white" title="Todos">
				<CheckSquare class="h-5 w-5" />
			</a>
			<a href="/settings" class="p-2 text-zinc-400 hover:text-white" title="Settings">
				<Settings class="h-5 w-5" />
			</a>
		</div>
		<div class="mt-auto flex flex-col items-center gap-2 border-t border-zinc-800 py-3">
			<ThemeToggleButton />
			<button onclick={handleSignOut} class="p-2 text-zinc-400 hover:text-white" title="Sign out">
				<LogOut class="h-4 w-4" />
			</button>
		</div>
	{:else}
		<!-- Expanded: full sidebar -->
		<div class="flex h-14 items-center justify-between px-5">
			<h1 class="text-lg font-semibold tracking-tight text-white">NotesApp</h1>
			{#if oncollapse}
				<button onclick={oncollapse} class="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300" title="Collapse">
					<PanelLeftClose class="h-4 w-4" />
				</button>
			{/if}
		</div>
		<AppSidebarNav {foldersStore} {tagsStore} />
		<div class="border-t border-zinc-800 px-4 py-3">
			<div class="flex items-center justify-between gap-2">
				<span class="truncate text-xs text-zinc-500">{authStore.user?.display_name ?? 'Loading...'}</span>
				<div class="flex shrink-0 items-center gap-1">
					<ThemeToggleButton />
					<button onclick={handleSignOut} class="rounded p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300" title="Sign out">
						<LogOut class="h-3.5 w-3.5" />
					</button>
				</div>
			</div>
		</div>
	{/if}
</aside>
