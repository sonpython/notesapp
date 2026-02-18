<script lang="ts">
	/**
	 * Resizable app layout with sidebar, divider, and main content.
	 * Sidebar width is persisted to localStorage.
	 */
	import type { Snippet } from 'svelte';
	import { PanelLeftClose, PanelLeft } from 'lucide-svelte';
	import AppSidebar from './app-sidebar.svelte';
	import AppHeader from './app-header.svelte';
	import ResizableDivider from '$lib/components/ui/resizable-divider.svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	const SIDEBAR_WIDTH_KEY = 'notesapp-sidebar-width';
	const SIDEBAR_COLLAPSED_KEY = 'notesapp-sidebar-collapsed';
	const DEFAULT_SIDEBAR_WIDTH = 256;
	const MIN_SIDEBAR_WIDTH = 200;
	const MAX_SIDEBAR_WIDTH = 400;

	let sidebarWidth = $state(DEFAULT_SIDEBAR_WIDTH);
	let sidebarCollapsed = $state(false);

	// Load persisted state after mount
	$effect(() => {
		const savedWidth = localStorage.getItem(SIDEBAR_WIDTH_KEY);
		if (savedWidth) sidebarWidth = parseInt(savedWidth, 10);
		const savedCollapsed = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
		if (savedCollapsed) sidebarCollapsed = savedCollapsed === 'true';
	});

	function toggleSidebar() {
		sidebarCollapsed = !sidebarCollapsed;
		localStorage.setItem(SIDEBAR_COLLAPSED_KEY, sidebarCollapsed.toString());
	}

	function handleSidebarResize(newWidth: number) {
		const clamped = Math.max(MIN_SIDEBAR_WIDTH, Math.min(MAX_SIDEBAR_WIDTH, newWidth));
		sidebarWidth = clamped;
		localStorage.setItem(SIDEBAR_WIDTH_KEY, clamped.toString());
	}
</script>

<div class="flex h-screen flex-col bg-background">
	<!-- Mobile header with menu toggle -->
	<AppHeader />

	<div class="flex flex-1 overflow-hidden">
		<!-- Desktop sidebar - hidden on mobile, collapsible -->
		{#if !sidebarCollapsed}
			<div class="hidden lg:flex" style="width: {sidebarWidth}px;">
				<AppSidebar />
			</div>
			<ResizableDivider onresize={handleSidebarResize} class="hidden lg:block" />
		{/if}

		<!-- Main content -->
		<main class="flex flex-1 flex-col overflow-hidden">
			<!-- Collapse toggle -->
			<div class="hidden h-10 items-center border-b border-border px-2 lg:flex">
				<button
					type="button"
					onclick={toggleSidebar}
					class="rounded p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
					title={sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
				>
					{#if sidebarCollapsed}
						<PanelLeft class="h-4 w-4" />
					{:else}
						<PanelLeftClose class="h-4 w-4" />
					{/if}
				</button>
			</div>
			<div class="flex flex-1 overflow-hidden">
				{@render children()}
			</div>
		</main>
	</div>
</div>
