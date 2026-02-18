<script lang="ts">
	/**
	 * Resizable app layout with sidebar, divider, and main content.
	 * Sidebar width is persisted to localStorage.
	 */
	import type { Snippet } from 'svelte';
	import AppSidebar from './app-sidebar.svelte';
	import AppHeader from './app-header.svelte';
	import ResizableDivider from '$lib/components/ui/resizable-divider.svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	const SIDEBAR_WIDTH_KEY = 'notesapp-sidebar-width';
	const DEFAULT_SIDEBAR_WIDTH = 256;
	const MIN_SIDEBAR_WIDTH = 200;
	const MAX_SIDEBAR_WIDTH = 400;

	let sidebarWidth = $state(DEFAULT_SIDEBAR_WIDTH);

	// Load persisted width after mount
	$effect(() => {
		const saved = localStorage.getItem(SIDEBAR_WIDTH_KEY);
		if (saved) sidebarWidth = parseInt(saved, 10);
	});

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
		<!-- Desktop sidebar - hidden on mobile -->
		<div class="hidden lg:flex" style="width: {sidebarWidth}px;">
			<AppSidebar />
		</div>

		<!-- Resizable divider - hidden on mobile -->
		<ResizableDivider onresize={handleSidebarResize} class="hidden lg:block" />

		<!-- Main content: note list + editor panes -->
		<main class="flex flex-1 overflow-hidden">
			{@render children()}
		</main>
	</div>
</div>
