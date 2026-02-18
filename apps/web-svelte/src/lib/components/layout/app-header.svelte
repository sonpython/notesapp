<script lang="ts">
	/**
	 * Mobile/tablet header with menu toggle for the sidebar.
	 * Hidden on desktop screens (lg:hidden).
	 */
	import { Menu, X } from 'lucide-svelte';
	import AppSidebar from './app-sidebar.svelte';
	import ThemeToggleButton from '$lib/components/ui/theme-toggle-button.svelte';

	let sidebarOpen = $state(false);
</script>

<!-- Header bar - visible on mobile/tablet only -->
<header class="flex h-12 items-center justify-between border-b border-border bg-background px-4 lg:hidden">
	<h1 class="text-sm font-semibold text-foreground">NotesApp</h1>
	<div class="flex items-center gap-2">
		<ThemeToggleButton />
		<button
			type="button"
			onclick={() => (sidebarOpen = !sidebarOpen)}
			class="rounded-md p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
			aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
		>
			{#if sidebarOpen}
				<X class="h-5 w-5" />
			{:else}
				<Menu class="h-5 w-5" />
			{/if}
		</button>
	</div>
</header>

<!-- Mobile sidebar overlay -->
{#if sidebarOpen}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-40 bg-black/60 lg:hidden"
		onclick={() => (sidebarOpen = false)}
		aria-hidden="true"
	></div>
	<!-- Sidebar panel -->
	<div class="fixed inset-y-0 left-0 z-50 w-64 lg:hidden">
		<AppSidebar />
	</div>
{/if}
