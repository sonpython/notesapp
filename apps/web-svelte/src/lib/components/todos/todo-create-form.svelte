<script lang="ts">
  import { Plus, Calendar, Bell } from 'lucide-svelte';
  import type { Todo } from '$lib/types';
  import RecurrenceSelector from './recurrence-selector.svelte';

  interface Props {
    oncreated: (todo: Todo) => void;
    parentId?: string;
  }

  let { oncreated, parentId }: Props = $props();

  let title = $state('');
  let priority = $state(0);
  let deadline = $state('');
  let reminderAt = $state('');
  let recurrenceType = $state('none');
  let recurrenceInterval = $state(1);
  let recurrenceDays = $state('');
  let recurrenceEndDate = $state('');
  let showExtras = $state(false);
  let submitting = $state(false);

  function resetForm() {
    title = '';
    priority = 0;
    deadline = '';
    reminderAt = '';
    recurrenceType = 'none';
    recurrenceInterval = 1;
    recurrenceDays = '';
    recurrenceEndDate = '';
    showExtras = false;
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed || submitting) return;

    submitting = true;
    try {
      const payload: Record<string, unknown> = { title: trimmed, priority };
      if (deadline) payload.deadline = deadline;
      if (reminderAt) payload.reminder_at = reminderAt;
      if (parentId) payload.parent_id = parentId;
      if (recurrenceType !== 'none') {
        payload.recurrence_type = recurrenceType;
        payload.recurrence_interval = recurrenceInterval;
        if (recurrenceType === 'weekly' && recurrenceDays) {
          payload.recurrence_days = recurrenceDays;
        }
        if (recurrenceEndDate) payload.recurrence_end_date = recurrenceEndDate;
      }
      oncreated(payload as unknown as Todo);
      resetForm();
    } finally {
      submitting = false;
    }
  }

  function handleRecurrenceChange(data: { type: string; interval: number; days: string; endDate: string }) {
    recurrenceType = data.type;
    recurrenceInterval = data.interval;
    recurrenceDays = data.days;
    recurrenceEndDate = data.endDate;
  }
</script>

<form onsubmit={handleSubmit} class="flex flex-col gap-2">
  <div class="flex items-center gap-2">
    <button
      type="submit"
      disabled={!title.trim() || submitting}
      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md
        bg-accent text-black transition-opacity hover:opacity-90
        disabled:cursor-not-allowed disabled:opacity-40"
      aria-label="Add todo"
    >
      <Plus size={16} />
    </button>

    <input
      type="text"
      bind:value={title}
      placeholder={parentId ? 'Add subtask...' : 'New todo...'}
      class="h-8 flex-1 rounded-md border border-border bg-background px-3
        text-sm text-foreground placeholder:text-muted
        focus:outline-none focus:ring-1 focus:ring-accent"
    />

    <select
      bind:value={priority}
      class="h-8 rounded-md border border-border bg-background px-2
        text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
      aria-label="Priority"
    >
      <option value={0}>No priority</option>
      <option value={1}>Low</option>
      <option value={2}>Medium</option>
      <option value={3}>High</option>
    </select>

    <button
      type="button"
      onclick={() => (showExtras = !showExtras)}
      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md
        border border-border text-muted transition-colors hover:text-foreground"
      aria-label="More options"
    >
      <Calendar size={14} />
    </button>
  </div>

  {#if showExtras}
    <div class="ml-10 flex flex-col gap-3">
      <div class="flex flex-wrap items-center gap-3">
        <label class="flex items-center gap-1.5 text-xs text-muted">
          <Calendar size={12} />
          <input
            type="datetime-local"
            bind:value={deadline}
            class="h-7 rounded border border-border bg-background px-2
              text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </label>
        <label class="flex items-center gap-1.5 text-xs text-muted">
          <Bell size={12} />
          <input
            type="datetime-local"
            bind:value={reminderAt}
            class="h-7 rounded border border-border bg-background px-2
              text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </label>
      </div>
      <RecurrenceSelector
        recurrenceType={recurrenceType}
        interval={recurrenceInterval}
        days={recurrenceDays}
        endDate={recurrenceEndDate}
        onchange={handleRecurrenceChange}
      />
    </div>
  {/if}
</form>
