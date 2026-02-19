<script lang="ts">
	import { page } from '$app/stores';
	import { PUBLIC_API_URL } from '$env/static/public';
	import { Lock, Copy, Download, Check } from 'lucide-svelte';

	const API_URL = PUBLIC_API_URL || 'http://localhost:8000';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let requiresPassword = $state(false);
	let password = $state('');
	let note = $state<{ title: string; content: string; created_at: string; updated_at: string } | null>(null);
	let copied = $state(false);

	const pubId = $derived($page.params.id);

	$effect(() => {
		checkNote();
	});

	async function checkNote() {
		loading = true;
		error = null;
		try {
			const res = await fetch(`${API_URL}/api/pub/${pubId}/check`);
			if (!res.ok) {
				const data = await res.json();
				error = data.detail || 'Note not found';
				loading = false;
				return;
			}
			const data = await res.json();
			requiresPassword = data.requires_password;
			if (!requiresPassword) {
				await viewNote();
			} else {
				loading = false;
			}
		} catch {
			error = 'Failed to load note';
			loading = false;
		}
	}

	async function viewNote() {
		loading = true;
		try {
			const fetchOptions: RequestInit = { method: 'POST' };
			if (password) {
				fetchOptions.headers = { 'Content-Type': 'application/json' };
				fetchOptions.body = JSON.stringify({ password });
			}
			const res = await fetch(`${API_URL}/api/pub/${pubId}/view`, fetchOptions);
			if (!res.ok) {
				const data = await res.json();
				error = data.detail || 'Failed to view note';
				loading = false;
				return;
			}
			note = await res.json();
		} catch {
			error = 'Failed to load note';
		}
		loading = false;
	}

	async function handlePasswordSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = null;
		await viewNote();
	}

	async function copyContent() {
		if (!note) return;
		// Strip HTML tags for plain text copy
		const text = note.content.replace(/<[^>]+>/g, '');
		await navigator.clipboard.writeText(text);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	async function importNote() {
		try {
			const res = await fetch(`${API_URL}/api/pub/${pubId}/import`, {
				method: 'POST',
				credentials: 'include',
			});
			if (res.ok) {
				const data = await res.json();
				alert(`Note imported: ${data.title}`);
			} else if (res.status === 401) {
				alert('Please login to import this note');
			} else {
				alert('Failed to import note');
			}
		} catch {
			alert('Failed to import note');
		}
	}
</script>

<svelte:head>
	<title>{note?.title || 'Shared Note'} - NotesApp</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<div class="mx-auto max-w-3xl px-4 py-8">
		{#if loading}
			<div class="flex justify-center py-20">
				<div class="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
			</div>
		{:else if error}
			<div class="rounded-lg border border-red-300 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20">
				<p class="text-red-700 dark:text-red-400">{error}</p>
				<a href="/login" class="mt-4 inline-block text-sm text-accent hover:underline">Go to login</a>
			</div>
		{:else if requiresPassword && !note}
			<div class="mx-auto max-w-sm">
				<div class="mb-6 text-center">
					<div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted/30">
						<Lock class="h-8 w-8 text-muted" />
					</div>
					<h1 class="text-xl font-semibold text-foreground">Password Protected</h1>
					<p class="mt-2 text-sm text-muted">This note requires a password to view.</p>
				</div>
				<form onsubmit={handlePasswordSubmit} class="space-y-4">
					<input
						type="password"
						bind:value={password}
						placeholder="Enter password"
						required
						class="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
					/>
					<button
						type="submit"
						class="h-10 w-full rounded-lg bg-accent text-sm font-medium text-black hover:opacity-90"
					>
						View Note
					</button>
				</form>
			</div>
		{:else if note}
			<article>
				<header class="mb-6 border-b border-border pb-4">
					<h1 class="text-2xl font-bold text-foreground">{note.title || 'Untitled'}</h1>
					<p class="mt-2 text-xs text-muted">
						Last updated: {new Date(note.updated_at).toLocaleDateString()}
					</p>
					<div class="mt-4 flex gap-2">
						<button
							onclick={copyContent}
							class="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:bg-muted/10"
						>
							{#if copied}
								<Check class="h-3.5 w-3.5" />
								Copied
							{:else}
								<Copy class="h-3.5 w-3.5" />
								Copy
							{/if}
						</button>
						<button
							onclick={importNote}
							class="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:bg-muted/10"
						>
							<Download class="h-3.5 w-3.5" />
							Import to my notes
						</button>
					</div>
				</header>
				<div class="prose prose-sm dark:prose-invert max-w-none">
					{@html note.content}
				</div>
			</article>
		{/if}
	</div>
</div>
