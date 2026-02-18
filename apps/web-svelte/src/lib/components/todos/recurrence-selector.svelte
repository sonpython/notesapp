<script lang="ts">
  import { Repeat } from 'lucide-svelte';

  interface RecurrenceData {
    type: string;
    interval: number;
    days: string;
    endDate: string;
  }

  interface Props {
    recurrenceType: string;
    interval: number;
    days: string;
    endDate: string;
    onchange: (data: RecurrenceData) => void;
  }

  let { recurrenceType, interval, days, endDate, onchange }: Props = $props();

  const WEEKDAYS = [
    { short: 'M', full: 'Monday', value: 'mon' },
    { short: 'T', full: 'Tuesday', value: 'tue' },
    { short: 'W', full: 'Wednesday', value: 'wed' },
    { short: 'T', full: 'Thursday', value: 'thu' },
    { short: 'F', full: 'Friday', value: 'fri' },
    { short: 'S', full: 'Saturday', value: 'sat' },
    { short: 'S', full: 'Sunday', value: 'sun' },
  ];

  const selectedDays = $derived(days ? days.split(',') : []);

  function toggleDay(day: string) {
    const next = selectedDays.includes(day)
      ? selectedDays.filter((d) => d !== day)
      : [...selectedDays, day];
    onchange({ type: recurrenceType, interval, days: next.join(','), endDate });
  }

  function handleTypeChange(newType: string) {
    onchange({
      type: newType,
      interval: newType === 'none' ? 1 : interval,
      days: newType === 'weekly' ? days : '',
      endDate: newType === 'none' ? '' : endDate,
    });
  }
</script>

<div class="flex flex-col gap-3">
  <!-- Type selector -->
  <label class="flex items-center gap-1.5 text-xs text-muted">
    <Repeat size={12} />
    <select
      value={recurrenceType}
      onchange={(e) => handleTypeChange((e.target as HTMLSelectElement).value)}
      class="h-7 rounded border border-border bg-background px-2
        text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
    >
      <option value="none">No repeat</option>
      <option value="daily">Daily</option>
      <option value="weekly">Weekly</option>
      <option value="monthly">Monthly</option>
    </select>
  </label>

  {#if recurrenceType !== 'none'}
    <!-- Interval -->
    <label class="flex items-center gap-1.5 text-xs text-muted">
      <span>Every</span>
      <input
        type="number"
        min="1"
        max="99"
        value={interval}
        oninput={(e) =>
          onchange({
            type: recurrenceType,
            interval: parseInt((e.target as HTMLInputElement).value) || 1,
            days,
            endDate,
          })}
        class="h-7 w-16 rounded border border-border bg-background px-2
          text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
      />
      <span>{recurrenceType}{interval > 1 ? 's' : ''}</span>
    </label>

    <!-- Weekday toggles (weekly only) -->
    {#if recurrenceType === 'weekly'}
      <div class="flex items-center gap-1.5 text-xs text-muted">
        <span>On:</span>
        <div class="flex gap-1">
          {#each WEEKDAYS as day (day.value)}
            <button
              type="button"
              onclick={() => toggleDay(day.value)}
              title={day.full}
              class="flex h-6 w-6 items-center justify-center rounded border text-xs transition-colors
                {selectedDays.includes(day.value)
                  ? 'border-accent bg-accent text-black'
                  : 'border-border bg-background text-muted hover:border-foreground'}"
            >
              {day.short}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- End date -->
    <label class="flex items-center gap-1.5 text-xs text-muted">
      <span>Until</span>
      <input
        type="date"
        value={endDate}
        onchange={(e) =>
          onchange({
            type: recurrenceType,
            interval,
            days,
            endDate: (e.target as HTMLInputElement).value,
          })}
        class="h-7 rounded border border-border bg-background px-2
          text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
      />
      <span class="text-[10px]">(optional)</span>
    </label>
  {/if}
</div>
