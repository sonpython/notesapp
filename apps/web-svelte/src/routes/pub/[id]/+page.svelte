<script lang="ts">
	import { page } from '$app/stores';
	import { Lock, Copy, Check } from 'lucide-svelte';
	import { marked } from 'marked';

	/** Check if content looks like HTML (vs raw markdown) */
	function isHtml(text: string): boolean {
		return /<[a-z][\s\S]*>/i.test(text.trim());
	}

	/** Convert content to HTML - handles both raw markdown and existing HTML */
	function toHtml(content: string): string {
		if (!content) return '';
		if (isHtml(content)) return content;
		return marked.parse(content, { async: false, gfm: true, breaks: true }) as string;
	}

	const API_URL = '';

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
			const data = await res.json();
			// Rewrite image URLs to use public endpoint
			if (pubId) data.content = rewriteImageUrls(data.content, pubId);
			// Convert markdown to HTML if needed
			data.content = toHtml(data.content);
			note = data;
		} catch {
			error = 'Failed to load note';
		}
		loading = false;
	}

	function rewriteImageUrls(content: string, pubId: string): string {
		// Replace /api/images/{id} with /api/pub/{pubId}/image/{id}
		return content.replace(
			/src="([^"]*\/api\/images\/([^"]+))"/g,
			`src="${API_URL}/api/pub/${pubId}/image/$2"`
		);
	}

	async function handlePasswordSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = null;
		await viewNote();
	}

	async function copyContent() {
		if (!note) return;
		const text = note.content.replace(/<[^>]+>/g, '');
		await navigator.clipboard.writeText(text);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<svelte:head>
	<title>{note?.title || 'Shared Note'}</title>
</svelte:head>

<div class="min-h-screen bg-white dark:bg-zinc-900">
	{#if loading}
		<div class="flex h-screen items-center justify-center">
			<div class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
		</div>
	{:else if error}
		<div class="flex h-screen flex-col items-center justify-center px-4">
			<p class="text-lg text-red-500">{error}</p>
		</div>
	{:else if requiresPassword && !note}
		<div class="flex h-screen items-center justify-center px-4">
			<div class="w-full max-w-sm">
				<div class="mb-6 text-center">
					<Lock class="mx-auto mb-4 h-12 w-12 text-zinc-400" />
					<h1 class="text-xl font-semibold text-zinc-900 dark:text-white">Password Protected</h1>
					<p class="mt-2 text-sm text-zinc-500">Enter password to view this note.</p>
				</div>
				<form onsubmit={handlePasswordSubmit} class="space-y-4">
					<input
						type="password"
						bind:value={password}
						placeholder="Password"
						required
						class="h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
					/>
					<button
						type="submit"
						class="h-10 w-full rounded-lg bg-blue-500 text-sm font-medium text-white hover:bg-blue-600"
					>
						View Note
					</button>
				</form>
			</div>
		</div>
	{:else if note}
		<article class="mx-auto max-w-3xl px-6 py-12">
			<header class="mb-8">
				<h1 class="text-3xl font-bold text-zinc-900 dark:text-white">{note.title || 'Untitled'}</h1>
				<div class="mt-3 flex items-center gap-4 text-sm text-zinc-500">
					<span>Updated {new Date(note.updated_at).toLocaleDateString()}</span>
					<button
						onclick={copyContent}
						class="flex items-center gap-1 hover:text-zinc-700 dark:hover:text-zinc-300"
					>
						{#if copied}
							<Check class="h-4 w-4" /> Copied
						{:else}
							<Copy class="h-4 w-4" /> Copy
						{/if}
					</button>
				</div>
			</header>
			<div class="prose prose-zinc dark:prose-invert prose-table:border-collapse prose-th:border prose-th:border-zinc-300 prose-th:bg-zinc-100 prose-th:px-3 prose-th:py-2 prose-td:border prose-td:border-zinc-300 prose-td:px-3 prose-td:py-2 dark:prose-th:border-zinc-600 dark:prose-th:bg-zinc-800 dark:prose-td:border-zinc-600 prose-img:rounded-lg prose-pre:bg-zinc-900 prose-pre:text-zinc-100 prose-code:before:content-none prose-code:after:content-none max-w-none">
				{@html note.content}
			</div>
		</article>
	{/if}
</div>
