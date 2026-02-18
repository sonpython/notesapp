<script lang="ts">
  import { X } from 'lucide-svelte';

  interface Props {
    name: string;
    color: string;
    onremove?: () => void;
    size?: 'sm' | 'md';
  }

  let { name, color, onremove, size = 'sm' }: Props = $props();

  const sizeClasses = $derived(size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1');
</script>

<span
  class="inline-flex items-center gap-1.5 rounded-full {sizeClasses} font-medium"
  style="background-color: {color}20; color: {color};"
>
  <span class="w-1.5 h-1.5 rounded-full" style="background-color: {color};"></span>
  <span>{name}</span>
  {#if onremove}
    <button
      onclick={(e) => { e.stopPropagation(); onremove!(); }}
      class="hover:opacity-70 transition-opacity"
      aria-label="Remove {name} tag"
    >
      <X class="w-3 h-3" />
    </button>
  {/if}
</span>
