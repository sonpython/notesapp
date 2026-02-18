<script lang="ts">
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
	import { authStore } from '$lib/stores/auth-store.svelte';

	let { children }: { children: Snippet } = $props();

	onMount(() => {
		authStore.init();
	});
</script>

<div class="flex min-h-screen bg-background">
	{@render children()}
</div>
