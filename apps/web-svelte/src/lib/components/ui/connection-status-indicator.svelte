<script lang="ts">
	/**
	 * Connection status indicator - shows sync status with server.
	 * Green: online/synced, Yellow: syncing, Red: offline
	 * Text only shown on hover via tooltip.
	 */
	import { connectionStore } from '$lib/stores/connection-store.svelte';

	const statusConfig = {
		online: { color: 'bg-green-500', label: 'Connected' },
		syncing: { color: 'bg-amber-500', label: 'Syncing...' },
		offline: { color: 'bg-red-500', label: 'Offline' }
	} as const;

	const config = $derived(statusConfig[connectionStore.status]);
	const isPulsing = $derived(connectionStore.status === 'syncing');
</script>

<span class="relative flex h-2 w-2 cursor-default" title={config.label}>
	{#if isPulsing}
		<span class="absolute inline-flex h-full w-full animate-ping rounded-full {config.color} opacity-75"></span>
	{/if}
	<span class="relative inline-flex h-2 w-2 rounded-full {config.color}"></span>
</span>
