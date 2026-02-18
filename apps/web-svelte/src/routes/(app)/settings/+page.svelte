<script lang="ts">
	/**
	 * Settings page - tabbed interface.
	 * URL param: ?tab=account|tags|telegram|about
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth-store.svelte';
	import { TagsStore } from '$lib/stores/tags-store.svelte';
	import TagManagementList from '$lib/components/tags/tag-management-list.svelte';
	import TelegramSettings from '$lib/components/settings/telegram-settings.svelte';
	import type { Tag } from '$lib/types';

	const tagsStore = new TagsStore();

	type Tab = 'account' | 'tags' | 'telegram' | 'about';

	const TABS: { value: Tab; label: string }[] = [
		{ value: 'account', label: 'Account' },
		{ value: 'tags', label: 'Tags' },
		{ value: 'telegram', label: 'Telegram' },
		{ value: 'about', label: 'About' }
	];

	const activeTab = $derived<Tab>(
		($page.url.searchParams.get('tab') as Tab) ?? 'account'
	);

	onMount(() => {
		tagsStore.fetchTags();
	});

	function setTab(tab: Tab) {
		goto(`?tab=${tab}`, { replaceState: true });
	}

	async function handleSignOut() {
		await authStore.signOut();
		goto('/login');
	}

	async function handleCreateTag(name: string, color: string): Promise<Tag | null> {
		try {
			return await tagsStore.createTag(name, color);
		} catch {
			return null;
		}
	}

	async function handleUpdateTag(id: string, name: string, color: string): Promise<Tag | null> {
		try {
			return await tagsStore.updateTag(id, { name, color });
		} catch {
			return null;
		}
	}

	async function handleDeleteTag(id: string): Promise<boolean> {
		try {
			await tagsStore.deleteTag(id);
			return true;
		} catch {
			return false;
		}
	}
</script>

<svelte:head>
	<title>Settings - NotesApp</title>
</svelte:head>

<div class="flex h-full w-full flex-col overflow-hidden">
	<!-- Tab bar -->
	<div class="flex items-center gap-1 border-b border-border px-4 py-2">
		{#each TABS as tab (tab.value)}
			<button
				onclick={() => setTab(tab.value)}
				class="rounded-md px-3 py-1 text-sm transition-colors {activeTab === tab.value
					? 'bg-accent/15 font-medium text-accent'
					: 'text-muted hover:text-foreground'}"
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- Tab content -->
	<div class="flex-1 overflow-y-auto p-6">
		{#if activeTab === 'account'}
			<div class="max-w-md space-y-6">
				<h2 class="text-lg font-semibold text-foreground">Account</h2>

				<div class="rounded-lg border border-border bg-sidebar p-4">
					{#if authStore.loading}
						<p class="text-sm text-muted">Loading...</p>
					{:else if authStore.user}
						<p class="text-sm font-medium text-foreground">{authStore.user.display_name}</p>
						<p class="mt-0.5 text-xs text-muted">Passkey authentication</p>
					{:else}
						<p class="text-sm text-muted">Not signed in</p>
					{/if}
				</div>

				<button
					onclick={handleSignOut}
					class="w-full rounded-lg border border-red-300 px-4 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20"
				>
					Sign Out
				</button>
			</div>

		{:else if activeTab === 'tags'}
			<div class="max-w-lg">
				<TagManagementList
					tags={tagsStore.tags}
					oncreate={handleCreateTag}
					onupdate={handleUpdateTag}
					ondelete={handleDeleteTag}
				/>
			</div>

		{:else if activeTab === 'telegram'}
			<div class="max-w-md">
				<TelegramSettings />
			</div>

		{:else if activeTab === 'about'}
			<div class="max-w-md space-y-4">
				<h2 class="text-lg font-semibold text-foreground">About</h2>
				<div class="rounded-lg border border-border bg-sidebar p-4 space-y-2">
					<div class="flex items-center justify-between text-sm">
						<span class="text-muted">App</span>
						<span class="font-medium text-foreground">NotesApp</span>
					</div>
					<div class="flex items-center justify-between text-sm">
						<span class="text-muted">Version</span>
						<span class="font-medium text-foreground">1.0.0</span>
					</div>
					<div class="flex items-center justify-between text-sm">
						<span class="text-muted">Stack</span>
						<span class="font-medium text-foreground">SvelteKit + FastAPI</span>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
