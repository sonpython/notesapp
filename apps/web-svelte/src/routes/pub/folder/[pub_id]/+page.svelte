<script lang="ts">
	/**
	 * Public shared folder page.
	 *
	 * Reuses the main TodoList / TodoCreateForm / TodoEditModal components so
	 * the recipient experience matches the owner UI exactly. SharedFolderTodo
	 * payloads are adapted into the full Todo shape with neutral defaults for
	 * fields the public surface does not expose (tags, recurrence, reminders).
	 */
	import { page } from '$app/stores';
	import { Lock, RefreshCw, ArrowUpDown } from 'lucide-svelte';
	import {
		publicFolderApi,
		SharedFolderError,
		type SharedFolderTodo,
		type CreateTodoBody,
		type UpdateTodoBody
	} from '$lib/api/public-folder-api';
	import TodoList from '$lib/components/todos/todo-list.svelte';
	import TodoCreateForm from '$lib/components/todos/todo-create-form.svelte';
	import type { Todo } from '$lib/types';

	const pubId = $derived($page.params.pub_id ?? '');

	let phase = $state<'loading' | 'password' | 'loaded' | 'error'>('loading');
	let error = $state<string | null>(null);
	let toast = $state<string | null>(null);

	let folderName = $state('Shared Folder');
	let isEditable = $state(false);
	let todos = $state<SharedFolderTodo[]>([]);
	let reorderMode = $state(false);

	let passwordInput = $state('');
	let passwordSubmitting = $state(false);

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

	/** Walk the todo tree and return the matching node (used for optimistic-lock token lookup). */
	function findTodo(list: SharedFolderTodo[], id: string): SharedFolderTodo | null {
		for (const t of list) {
			if (t.id === id) return t;
			const found = findTodo(t.children ?? [], id);
			if (found) return found;
		}
		return null;
	}

	/** Replace a node in the tree by id, returning a new tree. */
	function replaceTodo(
		list: SharedFolderTodo[],
		updated: SharedFolderTodo
	): SharedFolderTodo[] {
		return list.map((t) => {
			if (t.id === updated.id) return { ...updated, children: t.children };
			if (t.children?.length) {
				return { ...t, children: replaceTodo(t.children, updated) };
			}
			return t;
		});
	}

	/** Remove a node from the tree by id. */
	function removeTodo(list: SharedFolderTodo[], id: string): SharedFolderTodo[] {
		return list
			.filter((t) => t.id !== id)
			.map((t) =>
				t.children?.length ? { ...t, children: removeTodo(t.children, id) } : t
			);
	}

	/** Insert a new subtask under its parent (top-level if parent_id null). */
	function insertTodo(
		list: SharedFolderTodo[],
		todo: SharedFolderTodo
	): SharedFolderTodo[] {
		if (todo.parent_id == null) {
			return [...list, todo];
		}
		return list.map((t) => {
			if (t.id === todo.parent_id) {
				return { ...t, children: [...(t.children ?? []), todo] };
			}
			if (t.children?.length) {
				return { ...t, children: insertTodo(t.children, todo) };
			}
			return t;
		});
	}

	/**
	 * Adapt a SharedFolderTodo into the full Todo shape consumed by TodoList /
	 * TodoItem / TodoEditModal. Public surface does not expose tags, recurrence,
	 * note links, or reminders, so these are filled with neutral defaults.
	 */
	function asTodo(t: SharedFolderTodo): Todo {
		return {
			id: t.id,
			user_id: '',
			title: t.title,
			description: t.description,
			is_completed: t.is_completed,
			completed_at: t.completed_at,
			deadline: t.deadline,
			parent_id: t.parent_id,
			note_id: null,
			folder_id: null,
			priority: t.priority,
			sort_order: t.sort_order,
			reminder_at: null,
			reminder_sent: false,
			recurrence_type: null,
			recurrence_interval: null,
			recurrence_days: null,
			recurrence_end_date: null,
			recurrence_parent_id: null,
			created_at: t.created_at,
			updated_at: t.updated_at,
			children: (t.children ?? []).map(asTodo),
			tags: []
		};
	}

	const adaptedTodos = $derived(todos.map(asTodo));

	// -- Mutation handlers wired to publicFolderApi -----------------------------

	async function handleToggle(id: string) {
		const node = findTodo(todos, id);
		if (!node) return;
		try {
			const updated = await publicFolderApi.toggleTodo(pubId, id, node.updated_at);
			todos = replaceTodo(todos, updated);
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 409) {
				showToast('Someone else just updated this. Refreshing...');
				await refresh();
			} else {
				showToast(e instanceof Error ? e.message : 'Failed to toggle');
			}
		}
	}

	async function handleDelete(id: string) {
		const node = findTodo(todos, id);
		if (!node) return;
		try {
			await publicFolderApi.deleteTodo(pubId, id, node.updated_at);
			todos = removeTodo(todos, id);
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 409) {
				showToast('This todo just changed. Refreshing...');
				await refresh();
			} else {
				showToast(e instanceof Error ? e.message : 'Failed to delete');
			}
		}
	}

	async function handleUpdate(id: string, data: Record<string, unknown>) {
		// TodoItem signals subtask creation via the magic '__create__' id.
		if (id === '__create__') {
			const payload = data as Partial<Todo> & { parent_id?: string };
			await createTodo({
				title: String(payload.title ?? ''),
				description: (payload.description ?? null) as string | null,
				priority: typeof payload.priority === 'number' ? payload.priority : 0,
				deadline: (payload.deadline ?? null) as string | null,
				parent_id: payload.parent_id ?? null
			});
			return;
		}

		const node = findTodo(todos, id);
		if (!node) return;
		const body: UpdateTodoBody = { expected_updated_at: node.updated_at };
		// Allow only the public-surface fields to pass through; reminder_at /
		// recurrence_* / tag_ids from the modal are silently dropped.
		const allowed = ['title', 'description', 'priority', 'deadline', 'is_completed'] as const;
		const bodyAny = body as unknown as Record<string, unknown>;
		for (const key of allowed) {
			if (key in data) {
				bodyAny[key] = data[key];
			}
		}
		try {
			const updated = await publicFolderApi.updateTodo(pubId, id, body);
			todos = replaceTodo(todos, updated);
		} catch (e) {
			if (e instanceof SharedFolderError && e.status === 409) {
				showToast('Someone else just edited this. Refreshing...');
				await refresh();
			} else {
				showToast(e instanceof Error ? e.message : 'Failed to update');
			}
		}
	}

	async function createTodo(body: CreateTodoBody) {
		try {
			const todo = await publicFolderApi.createTodo(pubId, body);
			todos = insertTodo(todos, todo);
		} catch (e) {
			showToast(e instanceof Error ? e.message : 'Failed to create todo');
		}
	}

	function handleTopLevelCreated(payload: Todo) {
		void createTodo({
			title: payload.title,
			description: payload.description,
			priority: payload.priority,
			deadline: payload.deadline ?? null,
			parent_id: null
		});
	}

	async function handleReorder(orderedIds: string[]) {
		// Optimistic local reorder for top-level only (matches main UI behavior)
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

<div class="min-h-screen bg-background text-foreground">
	{#if phase === 'loading'}
		<div class="flex h-screen items-center justify-center">
			<div
				class="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"
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
					<Lock class="mx-auto mb-4 h-12 w-12 text-muted" />
					<h1 class="text-xl font-semibold">Password Protected</h1>
					<p class="mt-2 text-sm text-muted">Enter password to access this folder.</p>
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
						class="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
					/>
					<button
						type="submit"
						disabled={passwordSubmitting}
						class="h-10 w-full rounded-lg bg-accent text-sm font-medium text-black hover:opacity-90 disabled:opacity-60"
					>
						{passwordSubmitting ? 'Unlocking...' : 'Unlock'}
					</button>
				</form>
			</div>
		</div>
	{:else if phase === 'loaded'}
		<div class="mx-auto flex h-screen max-w-3xl flex-col">
			<header class="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
				<div class="min-w-0">
					<h1 class="truncate text-lg font-semibold">{folderName}</h1>
					<p class="text-xs text-muted">
						{isEditable ? 'Editable share — anyone with the link can change todos.' : 'Read-only share.'}
					</p>
				</div>
				<div class="flex items-center gap-1">
					{#if isEditable}
						<button
							onclick={() => (reorderMode = !reorderMode)}
							class="flex items-center gap-1 rounded-md px-2 py-1 text-sm {reorderMode
								? 'bg-accent/15 text-accent'
								: 'text-muted hover:text-foreground'}"
							title="Toggle drag to reorder"
						>
							<ArrowUpDown class="h-3.5 w-3.5" />
						</button>
					{/if}
					<button
						onclick={refresh}
						class="flex h-8 w-8 items-center justify-center rounded-md text-muted hover:text-foreground"
						aria-label="Refresh"
					>
						<RefreshCw size={14} />
					</button>
				</div>
			</header>

			<div class="flex-1 overflow-y-auto p-4">
				{#if isEditable}
					<div class="mb-4">
						<TodoCreateForm oncreated={handleTopLevelCreated} />
					</div>
				{/if}

				<TodoList
					todos={adaptedTodos}
					ontoggle={handleToggle}
					onupdate={handleUpdate}
					ondelete={handleDelete}
					onreorder={isEditable ? handleReorder : undefined}
					reorderMode={isEditable && reorderMode}
				/>
			</div>
		</div>
	{/if}

	{#if toast}
		<div
			class="fixed bottom-4 right-4 z-50 max-w-sm rounded-lg border border-border bg-background px-4 py-3 text-sm shadow-lg"
		>
			{toast}
		</div>
	{/if}
</div>
