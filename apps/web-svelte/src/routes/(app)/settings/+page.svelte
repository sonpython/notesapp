<script lang="ts">
	import { Settings } from 'lucide-svelte';
	import { authStore } from '$lib/stores/auth-store.svelte';
	import { goto } from '$app/navigation';

	async function handleSignOut() {
		await authStore.signOut();
		goto('/login');
	}
</script>

<svelte:head>
	<title>Settings - NotesApp</title>
</svelte:head>

<div class="flex-1 p-8">
	<h1 class="text-2xl font-bold text-foreground mb-6">Settings</h1>

	<div class="max-w-md space-y-6">
		<div class="p-4 bg-sidebar rounded-lg border border-border">
			<h2 class="font-medium text-foreground mb-2">Account</h2>
			{#if authStore.user}
				<p class="text-sm text-muted">Signed in as {authStore.user.display_name}</p>
			{:else}
				<p class="text-sm text-muted">Loading...</p>
			{/if}
		</div>

		<button
			onclick={handleSignOut}
			class="w-full px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20 transition-colors"
		>
			Sign Out
		</button>
	</div>
</div>
