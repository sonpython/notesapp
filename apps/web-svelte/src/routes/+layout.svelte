<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from 'mode-watcher';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<svelte:window onkeydown={(e) => {
	if ((e.ctrlKey || e.metaKey) && e.key === 's') {
		e.preventDefault();
		window.dispatchEvent(new CustomEvent('app:save'));
	}
}} />

<ModeWatcher defaultMode="system" track={true} />

{@render children()}
