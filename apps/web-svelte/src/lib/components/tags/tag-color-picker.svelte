<script lang="ts">
  import { Check } from 'lucide-svelte';
  import { TAG_COLORS } from './tag-colors';

  interface Props {
    selected: string;
    onchange: (hex: string) => void;
  }

  let { selected, onchange }: Props = $props();
</script>

<div class="grid grid-cols-6 gap-2">
  {#each TAG_COLORS as color (color.hex)}
    <button
      type="button"
      onclick={() => onchange(color.hex)}
      class="w-8 h-8 rounded-full flex items-center justify-center hover:scale-110 transition-transform"
      style="background-color: {color.hex};"
      aria-label={color.name}
      title={color.name}
    >
      {#if selected === color.hex}
        <Check class="w-4 h-4 text-white drop-shadow-md" />
      {/if}
    </button>
  {/each}
</div>
