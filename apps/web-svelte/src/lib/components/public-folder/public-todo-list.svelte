<script lang="ts">
	import { flip } from 'svelte/animate';
	import { dndzone } from 'svelte-dnd-action';
	import type { SharedFolderTodo } from '$lib/api/public-folder-api';
	import PublicTodoRow from './public-todo-row.svelte';

	interface Props {
		todos: SharedFolderTodo[];
		editable: boolean;
		ontoggle?: (todo: SharedFolderTodo) => void;
		ondelete?: (todo: SharedFolderTodo) => void;
		oneditTitle?: (todo: SharedFolderTodo, title: string) => void;
		onreorder?: (orderedIds: string[]) => void;
	}

	let { todos, editable, ontoggle, ondelete, oneditTitle, onreorder }: Props = $props();

	const incompleteTodos = $derived(todos.filter((t) => !t.is_completed));
	const completedTodos = $derived(todos.filter((t) => t.is_completed));

	let dndItems = $state<SharedFolderTodo[]>([]);
	$effect(() => {
		dndItems = [...incompleteTodos];
	});

	const flipDurationMs = 200;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const dndOptions = $derived({
		items: dndItems,
		flipDurationMs,
		dropTargetStyle: {},
		dragHandleSelector: '[data-drag-handle]'
	} as any);

	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	function handleConsider(e: any) {
		dndItems = e.detail.items;
	}
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	function handleFinalize(e: any) {
		dndItems = e.detail.items;
		if (onreorder) onreorder(dndItems.map((t: SharedFolderTodo) => t.id));
	}
</script>

{#if !todos?.length}
	<div class="flex flex-col items-center justify-center py-16 text-zinc-500">
		<p class="text-sm">
			No todos yet.{editable ? ' Add one above.' : ''}
		</p>
	</div>
{:else}
	{#if incompleteTodos.length > 0}
		{#if editable && onreorder}
			<div
				class="flex flex-col divide-y divide-zinc-200 dark:divide-zinc-800"
				use:dndzone={dndOptions}
				onconsider={handleConsider}
				onfinalize={handleFinalize}
			>
				{#each dndItems as todo (todo.id)}
					<div animate:flip={{ duration: flipDurationMs }}>
						<PublicTodoRow
							{todo}
							{editable}
							dragHandle={true}
							ontoggle={() => ontoggle?.(todo)}
							ondelete={() => ondelete?.(todo)}
							oneditTitle={(title) => oneditTitle?.(todo, title)}
						/>
					</div>
				{/each}
			</div>
		{:else}
			<div class="flex flex-col divide-y divide-zinc-200 dark:divide-zinc-800">
				{#each incompleteTodos as todo (todo.id)}
					<PublicTodoRow
						{todo}
						{editable}
						ontoggle={() => ontoggle?.(todo)}
						ondelete={() => ondelete?.(todo)}
						oneditTitle={(title) => oneditTitle?.(todo, title)}
					/>
				{/each}
			</div>
		{/if}
	{/if}

	{#if completedTodos.length > 0}
		<div class="flex flex-col divide-y divide-zinc-200 dark:divide-zinc-800">
			{#each completedTodos as todo (todo.id)}
				<PublicTodoRow
					{todo}
					{editable}
					ontoggle={() => ontoggle?.(todo)}
					ondelete={() => ondelete?.(todo)}
					oneditTitle={(title) => oneditTitle?.(todo, title)}
				/>
			{/each}
		</div>
	{/if}
{/if}
