<script lang="ts">
	/**
	 * Mobile bottom navigation bar - app-like navigation for mobile devices.
	 * Shows on mobile only (lg:hidden).
	 */
	import { page } from '$app/stores';
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
</script>

<nav class="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-background/95 backdrop-blur-sm lg:hidden safe-area-bottom">
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
