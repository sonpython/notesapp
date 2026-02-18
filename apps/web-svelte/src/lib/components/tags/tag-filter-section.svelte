<script lang="ts">
  import { X } from 'lucide-svelte';
  import type { Tag } from '$lib/types';

  interface Props {
    tags: Tag[];
    selectedTagIds: string[];
    ontoggleTag: (tagId: string) => void;
    onclearAll: () => void;
  }

  let { tags, selectedTagIds, ontoggleTag, onclearAll }: Props = $props();
</script>

{#if !tags?.length}
  <div class="text-xs text-zinc-500 italic px-2">No tags yet</div>
{:else}
  <div class="space-y-2">
    <div class="flex flex-wrap gap-1.5">
      {#each tags as tag (tag.id)}
        {@const isSelected = selectedTagIds.includes(tag.id)}
        <button
          onclick={() => ontoggleTag(tag.id)}
          class="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-all {isSelected
            ? 'ring-1 ring-offset-1 ring-offset-zinc-900'
            : 'opacity-70 hover:opacity-100'}"
          style="background-color: {tag.color}20; color: {tag.color};"
        >
          <span class="w-1.5 h-1.5 rounded-full" style="background-color: {tag.color};"></span>
          <span>{tag.name}</span>
        </button>
      {/each}
    </div>

    {#if selectedTagIds?.length > 0}
      <button
        onclick={onclearAll}
        class="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-400 transition-colors px-2"
      >
        <X class="w-3 h-3" />
        Clear filters
      </button>
    {/if}
  </div>
{/if}
