<script lang="ts">
	/**
	 * Theme toggle button - cycles light → dark → system.
	 * Uses mode-watcher for theme management.
	 */
	import { Moon, Sun } from 'lucide-svelte';
	import { mode, setMode } from 'mode-watcher';

	function handleToggle() {
		// Cycle: light → dark → system → light
		if ($mode === 'light') {
			setMode('dark');
		} else if ($mode === 'dark') {
			setMode('system');
		} else {
			setMode('light');
		}
	}

	const nextLabel = $derived(
		$mode === 'light' ? 'dark' : $mode === 'dark' ? 'system' : 'light'
	);
</script>

<button
	type="button"
	onclick={handleToggle}
	class="rounded-md p-1.5 text-muted transition-colors hover:bg-sidebar hover:text-foreground"
	aria-label="Switch to {nextLabel} theme"
	title="Current: {$mode}"
>
	{#if $mode === 'dark'}
		<Sun class="h-5 w-5" />
	{:else}
		<Moon class="h-5 w-5" />
	{/if}
</button>
