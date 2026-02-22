<script lang="ts">
  import {
    Check, Circle, Trash2, Bell, Repeat,
    ChevronRight, ChevronDown, Plus, Calendar, AlertCircle,
  } from 'lucide-svelte';
  import { format, isPast } from 'date-fns';
  import type { Todo } from '$lib/types';
  import TagPill from '$lib/components/tags/tag-pill.svelte';
  import TodoCreateForm from './todo-create-form.svelte';
  import TodoItemSelf from './todo-item.svelte';

  interface Props {
    todo: Todo;
    ontoggle: (id: string) => void;
    onupdate: (id: string, data: Record<string, unknown>) => void;
    ondelete: (id: string) => void;
    depth: number;
  }

  let { todo, ontoggle, onupdate, ondelete, depth }: Props = $props();

  let expanded = $state(false);
  let editing = $state(false);
  /** editTitle syncs to todo.title when editing starts; use $derived to track prop changes */
  let editTitle = $state('');
  let showSubtaskForm = $state(false);

  /** Color mapping for priority dot: 1=blue, 2=yellow, 3=red */
  const PRIORITY_COLORS: Record<number, string> = {
    1: 'bg-blue-500',
    2: 'bg-yellow-500',
    3: 'bg-red-500',
  };

  const hasChildren = $derived(todo.children && todo.children.length > 0);
  const isOverdue = $derived(
    !!todo.deadline && !todo.is_completed && isPast(new Date(todo.deadline))
  );

  /**
   * Format recurrence info into human-readable label.
   * Examples: "Daily", "Every 2 weeks (Mon, Wed)", "Monthly"
   */
  function formatRecurrenceLabel(t: Todo): string {
    if (!t.recurrence_type || t.recurrence_type === 'none') return '';
    const interval = t.recurrence_interval || 1;
    const type = t.recurrence_type;
    let label = interval === 1
      ? (type === 'daily' ? 'Daily' : type === 'weekly' ? 'Weekly' : 'Monthly')
      : `Every ${interval} ${type}${interval > 1 ? 's' : ''}`;
    if (type === 'weekly' && t.recurrence_days) {
      const dayMap: Record<string, string> = {
        mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu',
        fri: 'Fri', sat: 'Sat', sun: 'Sun',
      };
      const days = t.recurrence_days.split(',').map((d) => dayMap[d] || d).join(', ');
      label += ` (${days})`;
    }
    return label;
  }

  function startEdit() {
    editTitle = todo.title; // capture current value when edit begins
    editing = true;
  }

  function commitEdit() {
    const trimmed = editTitle.trim();
    if (trimmed && trimmed !== todo.title) {
      onupdate(todo.id, { title: trimmed });
    }
    editing = false;
  }

  function handleEditKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') commitEdit();
    if (e.key === 'Escape') editing = false;
  }

  function handleSubtaskCreated(data: Todo) {
    onupdate('__create__', { ...(data as unknown as Record<string, unknown>), parent_id: todo.id });
    showSubtaskForm = false;
  }
</script>

<div style="padding-left: {depth * 24}px">
  <!-- Main row -->
  <div class="group flex items-center gap-2 px-2 py-2 transition-colors hover:bg-sidebar">
    <!-- Expand/collapse toggle -->
    <button
      onclick={() => (expanded = !expanded)}
      class="flex h-5 w-5 shrink-0 items-center justify-center text-muted"
      aria-label={expanded ? 'Collapse' : 'Expand'}
    >
      {#if hasChildren}
        {#if expanded}
          <ChevronDown size={14} />
        {:else}
          <ChevronRight size={14} />
        {/if}
      {:else}
        <span class="w-3.5"></span>
      {/if}
    </button>

    <!-- Completion checkbox -->
    <button
      onclick={() => ontoggle(todo.id)}
      class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors
        {todo.is_completed
          ? 'border-accent bg-accent text-black'
          : 'border-muted text-transparent hover:border-foreground'}"
      aria-label={todo.is_completed ? 'Mark incomplete' : 'Mark complete'}
    >
      {#if todo.is_completed}
        <Check size={12} />
      {:else}
        <Circle size={12} />
      {/if}
    </button>

    <!-- Priority dot -->
    {#if todo.priority > 0}
      <span
        class="h-2 w-2 shrink-0 rounded-full {PRIORITY_COLORS[todo.priority] || ''}"
        title="Priority {todo.priority}"
      ></span>
    {/if}

    <!-- Tags (max 2 shown) -->
    {#if todo.tags && todo.tags.length > 0}
      <div class="flex items-center gap-1">
        {#each todo.tags.slice(0, 2) as tag (tag.id)}
          <TagPill name={tag.name} color={tag.color} size="sm" />
        {/each}
        {#if todo.tags.length > 2}
          <span class="text-[10px] text-muted/70">+{todo.tags.length - 2}</span>
        {/if}
      </div>
    {/if}

    <!-- Title (editable on double-click) -->
    {#if editing}
      <input
        bind:value={editTitle}
        onblur={commitEdit}
        onkeydown={handleEditKeydown}
        class="min-w-0 flex-1 rounded border border-accent bg-background px-2 py-0.5
          text-sm text-foreground outline-none"
      />
    {:else}
      <!-- role="button" satisfies a11y requirement for interactive non-button element -->
      <span
        role="button"
        tabindex="0"
        ondblclick={startEdit}
        onkeydown={(e) => e.key === 'Enter' && startEdit()}
        class="min-w-0 flex-1 cursor-default select-none break-words text-sm
          {todo.is_completed ? 'text-muted line-through' : 'text-foreground'}"
      >
        {todo.title}
      </span>
    {/if}

    <!-- Reminder indicator -->
    {#if todo.reminder_at}
      <span title="Reminder set">
        <Bell size={14} class="shrink-0 text-accent" />
      </span>
    {/if}

    <!-- Recurrence badge -->
    {#if todo.recurrence_type && todo.recurrence_type !== 'none'}
      <span
        class="flex shrink-0 items-center gap-1 text-xs text-muted"
        title={formatRecurrenceLabel(todo)}
      >
        <Repeat size={12} />
        <span class="hidden sm:inline">{formatRecurrenceLabel(todo)}</span>
      </span>
    {/if}

    <!-- Deadline -->
    {#if todo.deadline}
      <span
        class="flex shrink-0 items-center gap-1 text-xs {isOverdue ? 'text-red-500' : 'text-muted'}"
      >
        {#if isOverdue}<AlertCircle size={12} />{/if}
        <Calendar size={12} />
        {format(new Date(todo.deadline), 'MMM d')}
      </span>
    {/if}

    <!-- Add subtask button -->
    <button
      onclick={() => (showSubtaskForm = !showSubtaskForm)}
      class="flex h-6 w-6 shrink-0 items-center justify-center rounded text-muted
        opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
      aria-label="Add subtask"
    >
      <Plus size={14} />
    </button>

    <!-- Delete button -->
    <button
      onclick={() => ondelete(todo.id)}
      class="flex h-6 w-6 shrink-0 items-center justify-center rounded text-muted
        opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
      aria-label="Delete todo"
    >
      <Trash2 size={14} />
    </button>
  </div>

  <!-- Subtask creation form -->
  {#if showSubtaskForm}
    <div style="padding-left: {(depth + 1) * 24}px" class="px-2 pb-2">
      <TodoCreateForm oncreated={handleSubtaskCreated} parentId={todo.id} />
    </div>
  {/if}

  <!-- Recursive children -->
  {#if expanded && hasChildren}
    {#each todo.children! as child (child.id)}
      <TodoItemSelf
        todo={child}
        ontoggle={ontoggle}
        onupdate={onupdate}
        ondelete={ondelete}
        depth={depth + 1}
      />
    {/each}
  {/if}
</div>
