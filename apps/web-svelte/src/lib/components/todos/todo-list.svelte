<script lang="ts">
  import type { Todo } from '$lib/types';
  import TodoItem from './todo-item.svelte';

  interface Props {
    todos: Todo[];
    ontoggle: (id: string) => void;
    onupdate: (id: string, data: Record<string, unknown>) => void;
    ondelete: (id: string) => void;
  }

  let { todos, ontoggle, onupdate, ondelete }: Props = $props();
</script>

{#if todos.length === 0}
  <div class="flex flex-col items-center justify-center py-16 text-muted">
    <p class="text-sm">No todos yet. Create one above.</p>
  </div>
{:else}
  <div class="flex flex-col divide-y divide-border">
    {#each todos as todo (todo.id)}
      <TodoItem
        {todo}
        ontoggle={ontoggle}
        onupdate={onupdate}
        ondelete={ondelete}
        depth={0}
      />
    {/each}
  </div>
{/if}
