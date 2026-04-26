<script lang="ts">
	import { page } from '$app/stores';
	import { Lock, Plus, RefreshCw } from 'lucide-svelte';
	import {
		publicFolderApi,
		SharedFolderError,
		type SharedFolderTodo
	} from '$lib/api/public-folder-api';
	import PublicTodoList from '$lib/components/public-folder/public-todo-list.svelte';

	const pubId = $derived($page.params.pub_id ?? '');

	let phase = $state<'loading' | 'password' | 'loaded' | 'error'>('loading');
	let error = $state<string | null>(null);
	let toast = $state<string | null>(null);

	let folderName = $state('Shared Folder');
	let isEditable = $state(false);
	let todos = $state<SharedFolderTodo[]>([]);

	// Password form
	let passwordInput = $state('');
	let passwordSubmitting = $state(false);

	// Create form
	let newTitle = $state('');
	let newPriority = $state(0);
	let creating = $state(false);

	$effect(() => {
		void initialise();
	});

	async function initialise() {
		phase = 'loading';
		error = null;
		try {
			const info = await publicFolderApi.check(pubId);
			folderName = info.folder_name;
			isEditable = info.is_editable;
			if (info.requires_password) {
				phase = 'password';
				return;
			}
			await unlock();
		} catch (e) {
			error = e instanceof SharedFolderError ? e.message : 'Failed to load folder';
			phase = 'error';
		}
	}

	async function unlock(password?: string) {
		try {
			const data = await publicFolderApi.access(pubId, password);
			folderName = data.folder_name;
			isEditable = data.is_editable;
			todos = data.todos;
			phase = 'loaded';
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 401) {
				error = e.message;
				phase = 'password';
				return;
			}
			error = e instanceof SharedFolderError ? e.message : 'Failed to load folder';
			phase = 'error';
		}
	}

	async function handlePasswordSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = null;
		passwordSubmitting = true;
		await unlock(passwordInput);
		passwordSubmitting = false;
	}

	async function refresh() {
		try {
			todos = await publicFolderApi.listTodos(pubId);
		} catch (e) {
			showToast(e instanceof Error ? e.message : 'Failed to refresh');
		}
	}

	function showToast(msg: string) {
		toast = msg;
		setTimeout(() => (toast = null), 4000);
	}

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		const title = newTitle.trim();
		if (!title || creating || !isEditable) return;
		creating = true;
		try {
			const todo = await publicFolderApi.createTodo(pubId, { title, priority: newPriority });
			todos = [...todos, todo];
			newTitle = '';
			newPriority = 0;
		} catch (e) {
			showToast(e instanceof Error ? e.message : 'Failed to create todo');
		}
		creating = false;
	}

	async function handleToggle(todo: SharedFolderTodo) {
		try {
			const updated = await publicFolderApi.toggleTodo(pubId, todo.id, todo.updated_at);
			todos = todos.map((t) => (t.id === updated.id ? updated : t));
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 409) {
				showToast('Someone else just updated this. Refreshing...');
				await refresh();
			} else {
				showToast(e instanceof Error ? e.message : 'Failed to toggle todo');
			}
		}
	}

	async function handleDelete(todo: SharedFolderTodo) {
		if (!confirm(`Delete "${todo.title}"?`)) return;
		try {
			await publicFolderApi.deleteTodo(pubId, todo.id, todo.updated_at);
			todos = todos.filter((t) => t.id !== todo.id);
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 409) {
				showToast('This todo just changed. Refreshing...');
				await refresh();
			} else {
				showToast(e instanceof Error ? e.message : 'Failed to delete');
			}
		}
	}

	async function handleEditTitle(todo: SharedFolderTodo, title: string) {
		try {
			const updated = await publicFolderApi.updateTodo(pubId, todo.id, {
				expected_updated_at: todo.updated_at,
				title
			});
			todos = todos.map((t) => (t.id === updated.id ? updated : t));
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 409) {
				showToast('Someone else just edited this. Refreshing...');
				await refresh();
			} else {
				showToast(e instanceof Error ? e.message : 'Failed to update');
			}
		}
	}

	async function handleReorder(orderedIds: string[]) {
		// Apply optimistic ordering locally first
		const items = orderedIds.map((id, index) => ({ id, sort_order: index }));
		const completed = todos.filter((t) => t.is_completed);
		const reorderedIncomplete = orderedIds
			.map((id) => todos.find((t) => t.id === id))
			.filter((t): t is SharedFolderTodo => !!t)
			.map((t, index) => ({ ...t, sort_order: index }));
		todos = [...reorderedIncomplete, ...completed];
		try {
			await publicFolderApi.reorder(pubId, items);
		} catch (e) {
			showToast(e instanceof Error ? e.message : 'Reorder failed');
			await refresh();
		}
	}
</script>

<svelte:head>
	<title>{folderName} — Shared Folder</title>
</svelte:head>

<div class="min-h-screen bg-white dark:bg-zinc-900">
	{#if phase === 'loading'}
		<div class="flex h-screen items-center justify-center">
			<div
				class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"
			></div>
		</div>
	{:else if phase === 'error'}
		<div class="flex h-screen flex-col items-center justify-center px-4 text-center">
			<p class="text-lg text-red-500">{error || 'Something went wrong'}</p>
		</div>
	{:else if phase === 'password'}
		<div class="flex h-screen items-center justify-center px-4">
			<div class="w-full max-w-sm">
				<div class="mb-6 text-center">
					<Lock class="mx-auto mb-4 h-12 w-12 text-zinc-400" />
					<h1 class="text-xl font-semibold text-zinc-900 dark:text-white">Password Protected</h1>
					<p class="mt-2 text-sm text-zinc-500">Enter password to access this folder.</p>
					{#if error}
						<p class="mt-2 text-sm text-red-500">{error}</p>
					{/if}
				</div>
				<form onsubmit={handlePasswordSubmit} class="space-y-4">
					<input
						type="password"
						bind:value={passwordInput}
						placeholder="Password"
						required
						class="h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
					/>
					<button
						type="submit"
						disabled={passwordSubmitting}
						class="h-10 w-full rounded-lg bg-blue-500 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-60"
					>
						{passwordSubmitting ? 'Unlocking...' : 'Unlock'}
					</button>
				</form>
			</div>
		</div>
	{:else if phase === 'loaded'}
		<article class="mx-auto max-w-3xl px-6 py-10">
			<header class="mb-6 flex items-center justify-between gap-3">
				<div>
					<h1 class="text-2xl font-bold text-zinc-900 dark:text-white">{folderName}</h1>
					<p class="mt-1 text-xs text-zinc-500">
						{isEditable
							? 'Anyone with this link can edit todos in this folder.'
							: 'View-only shared folder.'}
					</p>
				</div>
				<button
					onclick={refresh}
					class="flex h-9 w-9 items-center justify-center rounded-full border border-zinc-300 text-zinc-500 hover:text-zinc-800 dark:border-zinc-700 dark:hover:text-zinc-200"
					aria-label="Refresh"
				>
					<RefreshCw size={14} />
				</button>
			</header>

			{#if isEditable}
				<form
					onsubmit={handleCreate}
					class="mb-6 flex items-center gap-2 rounded-lg border border-zinc-200 bg-white p-2 dark:border-zinc-800 dark:bg-zinc-800/50"
				>
					<button
						type="submit"
						disabled={!newTitle.trim() || creating}
						class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-40"
						aria-label="Add todo"
					>
						<Plus size={16} />
					</button>
					<input
						type="text"
						bind:value={newTitle}
						placeholder="New todo..."
						class="h-8 flex-1 rounded-md border border-zinc-300 bg-white px-3 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
					/>
					<select
						bind:value={newPriority}
						class="h-8 rounded-md border border-zinc-300 bg-white px-2 text-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-white"
						aria-label="Priority"
					>
						<option value={0}>No priority</option>
						<option value={1}>Low</option>
						<option value={2}>Medium</option>
						<option value={3}>High</option>
					</select>
				</form>
			{/if}

			<div class="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
				<PublicTodoList
					{todos}
					editable={isEditable}
					ontoggle={handleToggle}
					ondelete={handleDelete}
					oneditTitle={handleEditTitle}
					onreorder={isEditable ? handleReorder : undefined}
				/>
			</div>
		</article>
	{/if}

	{#if toast}
		<div
			class="fixed bottom-4 right-4 z-50 max-w-sm rounded-lg border border-zinc-300 bg-white px-4 py-3 text-sm text-zinc-800 shadow-lg dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
		>
			{toast}
		</div>
	{/if}
</div>
