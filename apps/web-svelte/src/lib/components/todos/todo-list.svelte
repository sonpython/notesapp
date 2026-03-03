<script lang="ts">
  import { flip } from 'svelte/animate';
  import { dndzone } from 'svelte-dnd-action';
  import { GripVertical } from 'lucide-svelte';
  import type { Todo } from '$lib/types';
  import TodoItem from './todo-item.svelte';

  interface Props {
    todos: Todo[];
    ontoggle: (id: string) => void;
    onupdate: (id: string, data: Record<string, unknown>) => void;
    ondelete: (id: string) => void;
    onreorder?: (orderedIds: string[]) => void;
    reorderMode?: boolean;
  }

  let { todos, ontoggle, onupdate, ondelete, onreorder, reorderMode = false }: Props = $props();

  // Split todos into incomplete (draggable) and completed (static)
  const incompleteTodos = $derived(todos.filter(t => !t.is_completed));
  const completedTodos = $derived(todos.filter(t => t.is_completed));

  // Local state for dnd-zone (needs mutable array)
  let dndItems = $state<Todo[]>([]);
  $effect(() => { dndItems = [...incompleteTodos]; });

  function handleDndConsider(e: CustomEvent<{ items: Todo[] }> | any) {
    dndItems = e.detail.items;
  }

  function handleDndFinalize(e: CustomEvent<{ items: Todo[] }> | any) {
    dndItems = e.detail.items;
    if (onreorder) {
      onreorder(dndItems.map((t: Todo) => t.id));
    }
  }

  const flipDurationMs = 200;

  // dragHandleSelector exists at runtime but is missing from the library's type defs
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dndOptions = $derived({
    items: dndItems,
    flipDurationMs,
    dropTargetStyle: {},
    dragHandleSelector: '[data-drag-handle]',
  } as any);
</script>

{#if !todos?.length}
  <div class="flex flex-col items-center justify-center py-16 text-muted">
    <p class="text-sm">No todos yet. Create one above.</p>
  </div>
{:else}
  <!-- Incomplete todos -->
  {#if incompleteTodos.length > 0}
    {#if reorderMode}
      <!-- Draggable mode -->
      <div
        class="flex flex-col divide-y divide-border"
        use:dndzone={dndOptions}
        onconsider={handleDndConsider}
        onfinalize={handleDndFinalize}
      >
        {#each dndItems as todo (todo.id)}
          <div class="group relative flex items-center" animate:flip={{ duration: flipDurationMs }}>
            <button
              data-drag-handle
              class="flex h-8 w-6 shrink-0 cursor-grab items-center justify-center text-muted
                hover:text-foreground active:cursor-grabbing"
              aria-label="Drag to reorder"
            >
              <GripVertical size={14} />
            </button>
            <div class="min-w-0 flex-1">
              <TodoItem {todo} {ontoggle} {onupdate} {ondelete} depth={0} />
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <!-- Static mode - no drag and drop -->
      <div class="flex flex-col divide-y divide-border">
        {#each incompleteTodos as todo (todo.id)}
          <TodoItem {todo} {ontoggle} {onupdate} {ondelete} depth={0} />
        {/each}
      </div>
    {/if}
  {/if}

  <!-- Completed todos - not draggable -->
  {#if completedTodos.length > 0}
    <div class="flex flex-col divide-y divide-border">
      {#each completedTodos as todo (todo.id)}
        <TodoItem
          {todo}
          {ontoggle}
          {onupdate}
          {ondelete}
          depth={0}
        />
      {/each}
    </div>
  {/if}
{/if}
