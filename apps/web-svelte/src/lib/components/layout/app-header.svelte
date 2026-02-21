<script lang="ts">
	/**
	 * Mobile/tablet header with search and menu toggle.
	 * Hidden on desktop screens (lg:hidden).
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Menu, X, Search, ArrowLeft } from 'lucide-svelte';
	import AppSidebar from './app-sidebar.svelte';

	interface Props {
		title?: string;
		showBack?: boolean;
		onback?: () => void;
	}
	let { title = 'NotesApp', showBack = false, onback }: Props = $props();

	let sidebarOpen = $state(false);
	let searchOpen = $state(false);
	let searchValue = $state('');

	// Sync search from URL
	$effect(() => {
		searchValue = $page.url.searchParams.get('search') ?? '';
	});

	function handleSearch(e: Event) {
		const value = (e.target as HTMLInputElement).value;
		searchValue = value;
		const params = new URLSearchParams($page.url.searchParams);
		if (value) {
			params.set('search', value);
		} else {
			params.delete('search');
		}
		goto(`${$page.url.pathname}?${params.toString()}`, { replaceState: true, keepFocus: true });
	}

	function closeSearch() {
		searchOpen = false;
		if (searchValue) {
			searchValue = '';
			const params = new URLSearchParams($page.url.searchParams);
			params.delete('search');
			goto(`${$page.url.pathname}?${params.toString()}`, { replaceState: true });
		}
	}

	function closeSidebar() {
		sidebarOpen = false;
	}
</script>

<!-- Header bar - visible on mobile/tablet only -->
<header class="flex h-14 items-center justify-between border-b border-border bg-background px-4 lg:hidden">
	{#if searchOpen}
		<!-- Search mode -->
		<div class="flex flex-1 items-center gap-2">
			<button onclick={closeSearch} class="p-2 text-muted hover:text-foreground">
				<ArrowLeft class="h-5 w-5" />
			</button>
			<input
				type="search"
				value={searchValue}
				oninput={handleSearch}
				placeholder="Search..."
				class="h-9 flex-1 rounded-lg border border-border bg-sidebar px-3 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
				autofocus
			/>
		</div>
	{:else}
		<!-- Normal mode -->
		<div class="flex items-center gap-2">
			{#if showBack}
				<button onclick={onback} class="p-2 text-muted hover:text-foreground">
					<ArrowLeft class="h-5 w-5" />
				</button>
			{:else}
				<button
					type="button"
					onclick={() => (sidebarOpen = !sidebarOpen)}
					class="p-2 text-muted hover:text-foreground"
					aria-label="Open menu"
				>
					<Menu class="h-5 w-5" />
				</button>
			{/if}
			<h1 class="text-base font-semibold text-foreground">{title}</h1>
		</div>
		<div class="flex items-center gap-1">
			<button
				onclick={() => (searchOpen = true)}
				class="p-2 text-muted hover:text-foreground"
				aria-label="Search"
			>
				<Search class="h-5 w-5" />
			</button>
		</div>
	{/if}
</header>

<!-- Mobile sidebar overlay -->
{#if sidebarOpen}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		class="fixed inset-0 z-40 bg-black/60 lg:hidden"
		onclick={closeSidebar}
		aria-hidden="true"
	></div>
	<div class="fixed inset-y-0 left-0 z-50 w-72 lg:hidden">
		<AppSidebar />
	</div>
{/if}
