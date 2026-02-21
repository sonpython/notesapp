<script lang="ts">
	import { X, Link, Copy, Check, Trash2 } from 'lucide-svelte';

	const API_URL = '';

	interface Props {
		noteId: string;
		onclose: () => void;
	}

	let { noteId, onclose }: Props = $props();

	let loading = $state(true);
	let saving = $state(false);
	let shareInfo = $state<{
		pub_id: string;
		url: string;
		has_password: boolean;
		expires_at: string | null;
		max_views: number | null;
		view_count: number;
	} | null>(null);

	// Form fields
	let password = $state('');
	let expiresInHours = $state<number | null>(null);
	let maxViews = $state<number | null>(null);
	let copied = $state(false);

	$effect(() => {
		fetchShareInfo();
	});

	async function fetchShareInfo() {
		loading = true;
		try {
			const res = await fetch(`${API_URL}/api/notes/${noteId}/share`, {
				credentials: 'include',
			});
			if (res.ok) {
				const data = await res.json();
				shareInfo = data;
			}
		} catch {
			// No share info
		}
		loading = false;
	}

	async function handleShare() {
		saving = true;
		try {
			const res = await fetch(`${API_URL}/api/notes/${noteId}/share`, {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					password: password || null,
					expires_in_hours: expiresInHours,
					max_views: maxViews,
				}),
			});
			if (res.ok) {
				shareInfo = await res.json();
				password = '';
			}
		} catch {
			alert('Failed to create share link');
		}
		saving = false;
	}

	async function handleUnshare() {
		if (!confirm('Remove share link? Anyone with the link will no longer be able to view this note.')) return;
		try {
			await fetch(`${API_URL}/api/notes/${noteId}/share`, {
				method: 'DELETE',
				credentials: 'include',
			});
			shareInfo = null;
		} catch {
			alert('Failed to remove share link');
		}
	}

	function getFullUrl() {
		if (!shareInfo) return '';
		return `${window.location.origin}/pub/${shareInfo.pub_id}`;
	}

	function getRawUrl() {
		if (!shareInfo) return '';
		return `${window.location.origin}/api/pub/${shareInfo.pub_id}/raw`;
	}

	async function copyLink() {
		await navigator.clipboard.writeText(getFullUrl());
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onclick={onclose}>
	<div
		class="w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-xl"
		onclick={(e) => e.stopPropagation()}
	>
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-lg font-semibold text-foreground">Share Note</h2>
			<button onclick={onclose} class="text-muted hover:text-foreground">
				<X class="h-5 w-5" />
			</button>
		</div>

		{#if loading}
			<div class="flex justify-center py-8">
				<div class="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
			</div>
		{:else if shareInfo}
			<!-- Already shared -->
			<div class="space-y-4">
				<div class="rounded-lg border border-border bg-muted/10 p-3">
					<p class="mb-2 text-xs text-muted">Share link (formatted)</p>
					<div class="flex items-center gap-2">
						<input
							type="text"
							readonly
							value={getFullUrl()}
							class="h-9 flex-1 rounded border border-border bg-background px-2 text-sm"
						/>
						<button
							onclick={copyLink}
							class="flex h-9 w-9 items-center justify-center rounded border border-border hover:bg-muted/20"
						>
							{#if copied}
								<Check class="h-4 w-4 text-green-500" />
							{:else}
								<Copy class="h-4 w-4" />
							{/if}
						</button>
					</div>
				</div>

				{#if !shareInfo.has_password}
				<div class="rounded-lg border border-border bg-muted/10 p-3">
					<p class="mb-2 text-xs text-muted">Raw text link (plain text, no formatting)</p>
					<div class="flex items-center gap-2">
						<input
							type="text"
							readonly
							value={getRawUrl()}
							class="h-9 flex-1 rounded border border-border bg-background px-2 text-sm"
						/>
						<button
							onclick={() => navigator.clipboard.writeText(getRawUrl())}
							class="flex h-9 w-9 items-center justify-center rounded border border-border hover:bg-muted/20"
						>
							<Copy class="h-4 w-4" />
						</button>
					</div>
				</div>
				{/if}

				<div class="flex items-center justify-between text-sm">
					<span class="text-muted">Views</span>
					<span class="text-foreground">
						{shareInfo.view_count}{shareInfo.max_views ? ` / ${shareInfo.max_views}` : ''}
					</span>
				</div>

				{#if shareInfo.expires_at}
					<div class="flex items-center justify-between text-sm">
						<span class="text-muted">Expires</span>
						<span class="text-foreground">{new Date(shareInfo.expires_at).toLocaleString()}</span>
					</div>
				{/if}

				<div class="flex items-center justify-between text-sm">
					<span class="text-muted">Password protected</span>
					<span class="text-foreground">{shareInfo.has_password ? 'Yes' : 'No'}</span>
				</div>

				<div class="flex gap-2 pt-2">
					<button
						onclick={handleUnshare}
						class="flex flex-1 items-center justify-center gap-2 rounded-lg border border-red-500/50 py-2 text-sm text-red-500 hover:bg-red-500/10"
					>
						<Trash2 class="h-4 w-4" />
						Remove link
					</button>
				</div>
			</div>
		{:else}
			<!-- Create share link -->
			<form onsubmit={(e) => { e.preventDefault(); handleShare(); }} class="space-y-4">
				<div>
					<label class="mb-1 block text-sm text-muted">Password (optional)</label>
					<input
						type="password"
						bind:value={password}
						placeholder="Leave empty for no password"
						class="h-9 w-full rounded border border-border bg-background px-3 text-sm"
					/>
				</div>

				<div>
					<label class="mb-1 block text-sm text-muted">Expire after (hours)</label>
					<select
						bind:value={expiresInHours}
						class="h-9 w-full rounded border border-border bg-background px-3 text-sm"
					>
						<option value={null}>Never</option>
						<option value={1}>1 hour</option>
						<option value={24}>1 day</option>
						<option value={168}>1 week</option>
						<option value={720}>30 days</option>
					</select>
				</div>

				<div>
					<label class="mb-1 block text-sm text-muted">Max views</label>
					<select
						bind:value={maxViews}
						class="h-9 w-full rounded border border-border bg-background px-3 text-sm"
					>
						<option value={null}>Unlimited</option>
						<option value={1}>1 view</option>
						<option value={10}>10 views</option>
						<option value={100}>100 views</option>
					</select>
				</div>

				<button
					type="submit"
					disabled={saving}
					class="flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-accent text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
				>
					<Link class="h-4 w-4" />
					{saving ? 'Creating...' : 'Create share link'}
				</button>
			</form>
		{/if}
	</div>
</div>
