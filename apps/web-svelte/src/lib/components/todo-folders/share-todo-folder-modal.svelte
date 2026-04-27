<script lang="ts">
	import { X, Link as LinkIcon, Copy, Check, Trash2 } from 'lucide-svelte';

	interface ShareInfo {
		pub_id: string;
		url: string;
		has_password: boolean;
		is_editable: boolean;
		expires_at: string | null;
		max_views: number | null;
		view_count: number;
	}

	interface Props {
		folderId: string;
		folderName: string;
		onclose: () => void;
	}

	let { folderId, folderName, onclose }: Props = $props();

	let loading = $state(true);
	let saving = $state(false);
	let shareInfo = $state<ShareInfo | null>(null);
	let copied = $state(false);

	// Form fields for creating / re-issuing the share
	let password = $state('');
	let expiresInHours = $state<number | null>(null);
	let maxViews = $state<number | null>(null);
	let isEditable = $state(false);

	$effect(() => {
		void fetchShareInfo();
	});

	async function fetchShareInfo() {
		loading = true;
		try {
			const res = await fetch(`/api/todo-folders/${folderId}/share`, {
				credentials: 'include'
			});
			if (res.ok) {
				const data = await res.json();
				shareInfo = data;
			}
		} catch {
			// no share yet — render the create form
		}
		loading = false;
	}

	async function handleShare() {
		saving = true;
		try {
			const res = await fetch(`/api/todo-folders/${folderId}/share`, {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					password: password || null,
					expires_in_hours: expiresInHours,
					max_views: maxViews,
					is_editable: isEditable
				})
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
		if (
			!confirm(
				'Remove share link? Anyone with the link will lose access immediately.'
			)
		)
			return;
		try {
			await fetch(`/api/todo-folders/${folderId}/share`, {
				method: 'DELETE',
				credentials: 'include'
			});
			shareInfo = null;
		} catch {
			alert('Failed to remove share link');
		}
	}

	function getFullUrl() {
		if (!shareInfo) return '';
		return `${window.location.origin}/pub/folder/${shareInfo.pub_id}`;
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
			<h2 class="text-lg font-semibold text-foreground">Share Folder</h2>
			<button onclick={onclose} class="text-muted hover:text-foreground" aria-label="Close">
				<X class="h-5 w-5" />
			</button>
		</div>
		<p class="mb-3 text-xs text-muted">Folder: <span class="text-foreground">{folderName}</span></p>

		{#if loading}
			<div class="flex justify-center py-8">
				<div
					class="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent"
				></div>
			</div>
		{:else if shareInfo}
			<!-- Already shared -->
			<div class="space-y-4">
				<div class="rounded-lg border border-border bg-muted/10 p-3">
					<p class="mb-2 text-xs text-muted">Share link</p>
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
							aria-label="Copy link"
						>
							{#if copied}
								<Check class="h-4 w-4 text-green-500" />
							{:else}
								<Copy class="h-4 w-4" />
							{/if}
						</button>
					</div>
				</div>

				<div class="space-y-1.5 text-sm">
					<div class="flex items-center justify-between">
						<span class="text-muted">Mode</span>
						<span class="text-foreground">
							{shareInfo.is_editable ? 'Editable (anyone can edit)' : 'Read-only'}
						</span>
					</div>
					<div class="flex items-center justify-between">
						<span class="text-muted">Views</span>
						<span class="text-foreground">
							{shareInfo.view_count}{shareInfo.max_views ? ` / ${shareInfo.max_views}` : ''}
						</span>
					</div>
					{#if shareInfo.expires_at}
						<div class="flex items-center justify-between">
							<span class="text-muted">Expires</span>
							<span class="text-foreground"
								>{new Date(shareInfo.expires_at).toLocaleString()}</span
							>
						</div>
					{/if}
					<div class="flex items-center justify-between">
						<span class="text-muted">Password protected</span>
						<span class="text-foreground">{shareInfo.has_password ? 'Yes' : 'No'}</span>
					</div>
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
			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleShare();
				}}
				class="space-y-4"
			>
				<label class="flex items-start gap-2 text-sm">
					<input
						type="checkbox"
						bind:checked={isEditable}
						class="mt-0.5 rounded border-border bg-background text-accent"
					/>
					<span>
						<span class="text-foreground">Allow editing</span>
						<span class="block text-xs text-muted">
							Anyone with the link can add, edit, complete, reorder, and delete todos.
						</span>
					</span>
				</label>

				<div>
					<label class="mb-1 block text-sm text-muted" for="share-folder-password"
						>Password (optional)</label
					>
					<input
						id="share-folder-password"
						type="password"
						bind:value={password}
						placeholder="Leave empty for no password"
						class="h-9 w-full rounded border border-border bg-background px-3 text-sm"
					/>
				</div>

				<div>
					<label class="mb-1 block text-sm text-muted" for="share-folder-expiry"
						>Expire after</label
					>
					<select
						id="share-folder-expiry"
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
					<label class="mb-1 block text-sm text-muted" for="share-folder-views"
						>Max views</label
					>
					<select
						id="share-folder-views"
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
					<LinkIcon class="h-4 w-4" />
					{saving ? 'Creating...' : 'Create share link'}
				</button>
			</form>
		{/if}
	</div>
</div>
