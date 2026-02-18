<script lang="ts">
	/**
	 * Todos page - filterable list with create form.
	 * URL params: tags (comma-separated IDs), filter (all|active|completed|overdue).
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { TodosStore, type TodoFilter } from '$lib/stores/todos-store.svelte';
	import { TagsStore } from '$lib/stores/tags-store.svelte';
	import TodoList from '$lib/components/todos/todo-list.svelte';
	import TodoCreateForm from '$lib/components/todos/todo-create-form.svelte';
	import TagFilterSection from '$lib/components/tags/tag-filter-section.svelte';
	import { Filter } from 'lucide-svelte';
	import type { Todo } from '$lib/types';

	const todosStore = new TodosStore();
	let showTagFilter = $state(false);
	const tagsStore = new TagsStore();

	// Derive URL params reactively
	const tagParam = $derived($page.url.searchParams.get('tags') ?? '');
	const selectedTagIds = $derived(tagParam ? tagParam.split(',').filter(Boolean) : []);
	const activeFilter = $derived<TodoFilter>(
		($page.url.searchParams.get('filter') as TodoFilter) ?? 'all'
	);

	// Fetch todos when URL params change
	$effect(() => {
		todosStore.fetchTodos(activeFilter, selectedTagIds.length ? selectedTagIds : undefined);
	});

	onMount(() => {
		tagsStore.fetchTags();
	});

	const FILTERS: { value: TodoFilter; label: string }[] = [
		{ value: 'all', label: 'All' },
		{ value: 'active', label: 'Active' },
		{ value: 'completed', label: 'Done' },
		{ value: 'overdue', label: 'Overdue' }
	];

	function setFilter(filter: TodoFilter) {
		const params = new URLSearchParams($page.url.searchParams);
		if (filter === 'all') {
			params.delete('filter');
		} else {
			params.set('filter', filter);
		}
		goto(`?${params.toString()}`, { replaceState: true });
	}

	function toggleTag(tagId: string) {
		const params = new URLSearchParams($page.url.searchParams);
		const current = tagParam ? tagParam.split(',').filter(Boolean) : [];
		const next = current.includes(tagId)
			? current.filter((id) => id !== tagId)
			: [...current, tagId];
		if (next.length) {
			params.set('tags', next.join(','));
		} else {
			params.delete('tags');
		}
		goto(`?${params.toString()}`, { replaceState: true });
	}

	function clearTagFilters() {
		const params = new URLSearchParams($page.url.searchParams);
		params.delete('tags');
		goto(`?${params.toString()}`, { replaceState: true });
	}

	async function handleCreated(todo: Todo) {
		await todosStore.createTodo({
			title: todo.title,
			description: todo.description ?? undefined,
			priority: todo.priority,
			deadline: todo.deadline ?? undefined,
			parent_id: todo.parent_id ?? undefined,
			reminder_at: todo.reminder_at ?? undefined,
			recurrence_type: todo.recurrence_type ?? undefined,
			recurrence_interval: todo.recurrence_interval ?? undefined,
			recurrence_days: todo.recurrence_days ?? undefined,
			recurrence_end_date: todo.recurrence_end_date ?? undefined
		});
	}

	async function handleToggle(id: string) {
		await todosStore.toggleTodo(id);
	}

	async function handleUpdate(id: string, data: Record<string, unknown>) {
		await todosStore.updateTodo(id, data);
	}

	async function handleDelete(id: string) {
		await todosStore.deleteTodo(id);
	}
</script>

<svelte:head>
	<title>Todos - NotesApp</title>
</svelte:head>

<div class="flex h-full w-full flex-col overflow-hidden">
	<!-- Toolbar: filter tabs -->
	<div class="flex items-center gap-1 border-b border-border px-4 py-2">
		{#each FILTERS as f (f.value)}
			<button
				onclick={() => setFilter(f.value)}
				class="rounded-md px-3 py-1 text-sm transition-colors {activeFilter === f.value
					? 'bg-accent/15 font-medium text-accent'
					: 'text-muted hover:text-foreground'}"
			>
				{f.label}
			</button>
		{/each}

		<!-- Tag filter button -->
		<div class="relative ml-auto flex items-center gap-2">
			{#if selectedTagIds.length > 0}
				<button onclick={clearTagFilters} class="text-xs text-muted hover:text-foreground">
					Clear ({selectedTagIds.length})
				</button>
			{/if}
			<button
				onclick={() => (showTagFilter = !showTagFilter)}
				class="flex items-center gap-1 rounded-md px-2 py-1 text-sm {selectedTagIds.length > 0 ? 'bg-accent/15 text-accent' : 'text-muted hover:text-foreground'}"
			>
				<Filter class="h-3.5 w-3.5" />
				Tags
			</button>
			{#if showTagFilter}
				<div class="absolute right-0 top-full mt-1 z-50 w-48 bg-zinc-800 border border-zinc-700 rounded-lg shadow-lg p-2">
					<TagFilterSection
						tags={tagsStore.tags ?? []}
						selectedTagIds={selectedTagIds}
						ontoggleTag={toggleTag}
						onclearAll={clearTagFilters}
					/>
				</div>
			{/if}
		</div>
		<span class="text-xs text-muted">{todosStore.total} item{todosStore.total !== 1 ? 's' : ''}</span>
	</div>

	<!-- Main content -->
	<div class="flex-1 overflow-y-auto p-4">
		<div class="mb-4">
			<TodoCreateForm oncreated={handleCreated} />
		</div>

		{#if todosStore.error}
			<p class="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
				{todosStore.error}
			</p>
		{/if}

		<TodoList
			todos={todosStore.todos}
			ontoggle={handleToggle}
			onupdate={handleUpdate}
			ondelete={handleDelete}
		/>
	</div>
</div>
