<script lang="ts">
	/**
	 * Mobile bottom navigation bar - app-like navigation for mobile devices.
	 * Shows on mobile only (lg:hidden).
	 * Auto-hides on scroll down, shows on scroll up.
	 */
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { FileText, CheckSquare, Settings, Tag } from 'lucide-svelte';

	const pathname = $derived($page.url.pathname);

	const navItems = [
		{ label: 'Notes', href: '/notes', icon: FileText },
		{ label: 'Tags', href: '/settings?tab=tags', icon: Tag },
		{ label: 'Todos', href: '/todos?filter=active', icon: CheckSquare },
		{ label: 'Settings', href: '/settings', icon: Settings },
	] as const;

	function isActive(href: string): boolean {
		if (href === '/notes') return pathname === '/notes';
		if (href.includes('tab=tags')) return pathname === '/settings' && $page.url.searchParams.get('tab') === 'tags';
		if (href === '/settings') return pathname === '/settings' && !$page.url.searchParams.has('tab');
		return pathname.startsWith(href.split('?')[0]);
	}

	// Scroll-based visibility using touch events (works with any scroll container)
	let isVisible = $state(true);
	let touchStartY = 0;
	let lastTouchY = 0;
	const TOUCH_THRESHOLD = 20; // Min touch distance to trigger hide/show

	$effect(() => {
		if (!browser) return;

		function handleTouchStart(e: TouchEvent) {
			touchStartY = e.touches[0].clientY;
			lastTouchY = touchStartY;
		}

		function handleTouchMove(e: TouchEvent) {
			const currentY = e.touches[0].clientY;
			const diff = currentY - lastTouchY;

			// Only trigger if movement exceeds threshold
			if (Math.abs(currentY - touchStartY) < TOUCH_THRESHOLD) return;

			// Moving finger up (scrolling down content) → hide
			// Moving finger down (scrolling up content) → show
			isVisible = diff > 0;
			lastTouchY = currentY;
		}

		document.addEventListener('touchstart', handleTouchStart, { passive: true });
		document.addEventListener('touchmove', handleTouchMove, { passive: true });

		return () => {
			document.removeEventListener('touchstart', handleTouchStart);
			document.removeEventListener('touchmove', handleTouchMove);
		};
	});
</script>

<nav
	class="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-background/95 backdrop-blur-sm lg:hidden safe-area-bottom transition-transform duration-300 ease-out"
	class:translate-y-full={!isVisible}>
	<div class="flex h-16 items-center justify-around px-2">
		{#each navItems as item (item.href)}
			{@const active = isActive(item.href)}
			<a
				href={item.href}
				class="flex flex-1 flex-col items-center justify-center gap-0.5 py-2 transition-colors
					{active ? 'text-accent' : 'text-muted hover:text-foreground'}"
			>
				<item.icon class="h-5 w-5" />
				<span class="text-[10px] font-medium">{item.label}</span>
			</a>
		{/each}
	</div>
</nav>

<style>
	.safe-area-bottom {
		padding-bottom: env(safe-area-inset-bottom, 0);
	}
</style>
