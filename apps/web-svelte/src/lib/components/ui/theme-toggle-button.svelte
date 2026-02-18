<script lang="ts">
	/**
	 * Theme toggle button - cycles light → dark → system.
	 * Uses mode-watcher for theme management.
	 */
	import { Moon, Sun, Monitor } from 'lucide-svelte';
	import { mode, userPrefersMode, setMode } from 'mode-watcher';

	function handleToggle() {
		// Cycle: light → dark → system → light
		// Use userPrefersMode to track actual user preference (mode is always resolved)
		const current = $userPrefersMode;
		if (current === 'light') {
			setMode('dark');
		} else if (current === 'dark') {
			setMode('system');
		} else {
			setMode('light');
		}
	}

	const currentPref = $derived($userPrefersMode);
	const resolvedMode = $derived($mode);
	const nextLabel = $derived(
		currentPref === 'light' ? 'dark' : currentPref === 'dark' ? 'system' : 'light'
	);
</script>

<button
	type="button"
	onclick={handleToggle}
	class="rounded-md p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
	aria-label="Switch to {nextLabel} theme"
	title="Current: {currentPref} (resolved: {resolvedMode})"
>
	{#if currentPref === 'system'}
		<Monitor class="h-5 w-5" />
	{:else if resolvedMode === 'dark'}
		<Sun class="h-5 w-5" />
	{:else}
		<Moon class="h-5 w-5" />
	{/if}
</button>
