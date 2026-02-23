<script lang="ts">
  /**
   * Modal for editing todo details (title, description, priority, deadline, etc.)
   */
  import { X, Calendar, Flag, Bell, Repeat } from 'lucide-svelte';
  import type { Todo } from '$lib/types';

  interface Props {
    todo: Todo;
    onsave: (data: Record<string, unknown>) => void;
    onclose: () => void;
  }

  let { todo, onsave, onclose }: Props = $props();

  // Form state
  let title = $state(todo.title);
  let description = $state(todo.description || '');
  let priority = $state(todo.priority);
  let deadline = $state(todo.deadline ? todo.deadline.slice(0, 10) : '');
  let reminderAt = $state(todo.reminder_at ? todo.reminder_at.slice(0, 16) : '');

  function handleSave() {
    onsave({
      title: title.trim(),
      description: description.trim() || null,
      priority,
      deadline: deadline || null,
      reminder_at: reminderAt || null,
    });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onclose();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) onclose();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
  onclick={handleBackdropClick}
>
  <div class="w-full max-w-md rounded-xl bg-background shadow-2xl">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-border px-4 py-3">
      <h2 class="text-lg font-semibold text-foreground">Edit Todo</h2>
      <button
        onclick={onclose}
        class="rounded p-1 text-muted hover:bg-sidebar hover:text-foreground"
      >
        <X size={20} />
      </button>
    </div>

    <!-- Body -->
    <div class="space-y-4 p-4">
      <!-- Title -->
      <div>
        <label class="mb-1 block text-xs font-medium text-muted">Title</label>
        <input
          bind:value={title}
          class="w-full rounded-lg border border-border bg-sidebar px-3 py-2 text-sm text-foreground
            placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder="Todo title"
        />
      </div>

      <!-- Description -->
      <div>
        <label class="mb-1 block text-xs font-medium text-muted">Description</label>
        <textarea
          bind:value={description}
          rows={3}
          class="w-full rounded-lg border border-border bg-sidebar px-3 py-2 text-sm text-foreground
            placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent resize-none"
          placeholder="Add notes..."
        ></textarea>
      </div>

      <!-- Priority -->
      <div>
        <label class="mb-1 block text-xs font-medium text-muted">
          <Flag size={12} class="inline mr-1" />Priority
        </label>
        <div class="flex gap-2">
          {#each [0, 1, 2, 3] as p}
            <button
              type="button"
              onclick={() => (priority = p)}
              class="flex-1 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors
                {priority === p
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border text-muted hover:bg-sidebar'}"
            >
              {p === 0 ? 'None' : p === 1 ? 'Low' : p === 2 ? 'Medium' : 'High'}
            </button>
          {/each}
        </div>
      </div>

      <!-- Deadline -->
      <div>
        <label class="mb-1 block text-xs font-medium text-muted">
          <Calendar size={12} class="inline mr-1" />Due Date
        </label>
        <input
          type="date"
          bind:value={deadline}
          class="w-full rounded-lg border border-border bg-sidebar px-3 py-2 text-sm text-foreground
            focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      <!-- Reminder -->
      <div>
        <label class="mb-1 block text-xs font-medium text-muted">
          <Bell size={12} class="inline mr-1" />Reminder
        </label>
        <input
          type="datetime-local"
          bind:value={reminderAt}
          class="w-full rounded-lg border border-border bg-sidebar px-3 py-2 text-sm text-foreground
            focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>
    </div>

    <!-- Footer -->
    <div class="flex justify-end gap-2 border-t border-border px-4 py-3">
      <button
        onclick={onclose}
        class="rounded-lg px-4 py-2 text-sm font-medium text-muted hover:bg-sidebar hover:text-foreground"
      >
        Cancel
      </button>
      <button
        onclick={handleSave}
        class="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
      >
        Save
      </button>
    </div>
  </div>
</div>
