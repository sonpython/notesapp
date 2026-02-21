<script lang="ts">
	/**
	 * Resizable app layout with sidebar, divider, and main content.
	 * Mobile: bottom nav + full-screen views. Desktop: sidebar + split pane.
	 */
	import type { Snippet } from 'svelte';
	import AppSidebar from './app-sidebar.svelte';
	import AppHeader from './app-header.svelte';
	import MobileBottomNav from './mobile-bottom-nav.svelte';
	import PwaInstallBanner from '$lib/components/ui/pwa-install-banner.svelte';
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
	let bottomNavVisible = $state(true);

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
	<!-- PWA install banner (mobile only) -->
	<PwaInstallBanner />

	<!-- Mobile header - hidden on desktop -->
	<AppHeader />

	<div class="flex flex-1 overflow-hidden">
		<!-- Desktop sidebar - hidden on mobile -->
		<div class="hidden lg:flex" style="width: {sidebarCollapsed ? '56px' : sidebarWidth + 'px'};">
			<AppSidebar oncollapse={toggleSidebar} collapsed={sidebarCollapsed} />
		</div>
		{#if !sidebarCollapsed}
			<ResizableDivider onresize={handleSidebarResize} class="hidden lg:block" />
		{/if}

		<!-- Main content - with bottom padding on mobile for nav (dynamic) -->
		<main class="flex flex-1 overflow-hidden transition-[padding] duration-300 lg:pb-0" class:pb-16={bottomNavVisible}>
			{@render children()}
		</main>
	</div>

	<!-- Mobile bottom navigation -->
	<MobileBottomNav bind:visible={bottomNavVisible} />
</div>
