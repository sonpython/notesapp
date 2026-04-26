<script lang="ts">
	import { Check, Circle, Trash2, Calendar, AlertCircle, GripVertical } from 'lucide-svelte';
	import { format, isPast } from 'date-fns';
	import type { SharedFolderTodo } from '$lib/api/public-folder-api';

	interface Props {
		todo: SharedFolderTodo;
		editable: boolean;
		dragHandle?: boolean;
		ontoggle?: () => void;
		ondelete?: () => void;
		oneditTitle?: (title: string) => void;
	}

	let { todo, editable, dragHandle = false, ontoggle, ondelete, oneditTitle }: Props = $props();

	const PRIORITY_COLORS: Record<number, string> = {
		1: 'bg-blue-500',
		2: 'bg-yellow-500',
		3: 'bg-red-500'
	};

	const isOverdue = $derived(
		!!todo.deadline && !todo.is_completed && isPast(new Date(todo.deadline))
	);

	let editing = $state(false);
	let draftTitle = $state('');

	function startEdit() {
		if (!editable || !oneditTitle) return;
		draftTitle = todo.title;
		editing = true;
	}

	function commitEdit() {
		const trimmed = draftTitle.trim();
		if (trimmed && trimmed !== todo.title && oneditTitle) {
			oneditTitle(trimmed);
		}
		editing = false;
	}

	function handleEditKey(e: KeyboardEvent) {
		if (e.key === 'Enter') commitEdit();
		else if (e.key === 'Escape') editing = false;
	}
</script>

<div
	class="group flex items-center gap-2 px-2 py-2 transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
>
	{#if dragHandle && editable}
		<button
			data-drag-handle
			class="flex h-5 w-5 shrink-0 cursor-grab items-center justify-center text-zinc-400 active:cursor-grabbing"
			aria-label="Drag to reorder"
		>
			<GripVertical size={14} />
		</button>
	{:else}
		<span class="w-5 shrink-0"></span>
	{/if}

	<button
		onclick={() => editable && ontoggle?.()}
		disabled={!editable}
		class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors
      {todo.is_completed
			? 'border-blue-500 bg-blue-500 text-white'
			: 'border-zinc-400 text-transparent hover:border-zinc-600'}
      {!editable ? 'cursor-default opacity-80' : ''}"
		aria-label={todo.is_completed ? 'Mark incomplete' : 'Mark complete'}
	>
		{#if todo.is_completed}
			<Check size={12} />
		{:else}
			<Circle size={12} />
		{/if}
	</button>

	{#if todo.priority > 0}
		<span
			class="h-2 w-2 shrink-0 rounded-full {PRIORITY_COLORS[todo.priority] || ''}"
			title="Priority {todo.priority}"
		></span>
	{/if}

	{#if editing}
		<input
			bind:value={draftTitle}
			onblur={commitEdit}
			onkeydown={handleEditKey}
			class="min-w-0 flex-1 rounded border border-blue-400 bg-white px-2 py-0.5 text-sm outline-none dark:bg-zinc-800 dark:text-white"
		/>
	{:else}
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<span
			role={editable ? 'button' : undefined}
			tabindex={editable ? 0 : -1}
			onclick={startEdit}
			onkeydown={(e) => editable && e.key === 'Enter' && startEdit()}
			class="min-w-0 flex-1 select-none break-words text-sm
        {todo.is_completed ? 'text-zinc-400 line-through' : 'text-zinc-900 dark:text-zinc-100'}
        {editable ? 'cursor-pointer' : ''}"
		>
			{todo.title}
		</span>
	{/if}

	{#if todo.deadline}
		<span
			class="flex shrink-0 items-center gap-1 text-xs {isOverdue ? 'text-red-500' : 'text-zinc-500'}"
		>
			{#if isOverdue}<AlertCircle size={12} />{/if}
			<Calendar size={12} />
			{format(new Date(todo.deadline), 'MMM d')}
		</span>
	{/if}

	{#if editable && ondelete}
		<button
			onclick={() => ondelete?.()}
			class="flex h-6 w-6 shrink-0 items-center justify-center rounded text-zinc-400
        opacity-100 transition-opacity hover:text-red-500 md:opacity-0 md:group-hover:opacity-100"
			aria-label="Delete todo"
		>
			<Trash2 size={14} />
		</button>
	{/if}
</div>
