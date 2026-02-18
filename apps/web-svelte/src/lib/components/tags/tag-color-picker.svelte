<script lang="ts">
  import { Check } from 'lucide-svelte';
  import { TAG_COLORS } from './tag-colors';

  interface Props {
    selected: string;
    onchange: (hex: string) => void;
    compact?: boolean;
  }

  let { selected, onchange, compact = false }: Props = $props();
</script>

<div class="grid gap-1.5 {compact ? 'grid-cols-8' : 'grid-cols-6 gap-2'}">
  {#each TAG_COLORS as color (color.hex)}
    <button
      type="button"
      onclick={() => onchange(color.hex)}
      class="rounded-full flex items-center justify-center hover:scale-110 transition-transform {compact ? 'w-5 h-5' : 'w-8 h-8'}"
      style="background-color: {color.hex};"
      aria-label={color.name}
      title={color.name}
    >
      {#if selected === color.hex}
        <Check class="{compact ? 'w-3 h-3' : 'w-4 h-4'} text-white drop-shadow-md" />
      {/if}
    </button>
  {/each}
</div>
