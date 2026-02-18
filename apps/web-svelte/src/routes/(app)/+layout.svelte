<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth-store.svelte';
	import ResizableAppLayout from '$lib/components/layout/resizable-app-layout.svelte';

	let { children }: { children: Snippet } = $props();

	onMount(() => {
		authStore.init();
	});
</script>

<ResizableAppLayout>
	{@render children()}
</ResizableAppLayout>
