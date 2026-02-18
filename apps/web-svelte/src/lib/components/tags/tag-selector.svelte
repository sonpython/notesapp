<script lang="ts">
  import { Plus, Search } from 'lucide-svelte';
  import type { Tag } from '$lib/types';
  import TagPill from './tag-pill.svelte';
  import TagColorPicker from './tag-color-picker.svelte';
  import { TAG_COLORS } from './tag-colors';

  interface Props {
    selectedTags: Tag[];
    allTags: Tag[];
    onadd: (tagId: string) => void;
    onremove: (tagId: string) => void;
    oncreate: (name: string, color: string) => Promise<Tag | null>;
  }

  let { selectedTags, allTags, onadd, onremove, oncreate }: Props = $props();

  let isOpen = $state(false);
  let search = $state('');
  let isCreating = $state(false);
  let newTagName = $state('');
  let newTagColor = $state(TAG_COLORS[0].hex);
  let dropdownRef = $state<HTMLDivElement | null>(null);
  let createError = $state<string | null>(null);

  const availableTags = $derived((allTags ?? []).filter((tag) => !(selectedTags ?? []).some((st) => st.id === tag.id)));
  const filteredTags = $derived(availableTags.filter((tag) => tag.name.toLowerCase().includes(search.toLowerCase())));

  $effect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
        isOpen = false;
        isCreating = false;
        createError = null;
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  });

  async function handleCreateTag() {
    if (!newTagName.trim()) return;
    createError = null;
    try {
      const created = await oncreate(newTagName.trim(), newTagColor);
      if (created) {
        onadd(created.id);
        newTagName = '';
        newTagColor = TAG_COLORS[0].hex;
        isCreating = false;
        search = '';
      }
    } catch (err) {
      // Handle 409 Conflict (duplicate tag name)
      if (err instanceof Error && err.message.includes('409')) {
        createError = 'Tag already exists';
      } else {
        createError = 'Failed to create tag';
      }
    }
  }
</script>

<div class="relative" bind:this={dropdownRef}>
  <!-- Selected tags display -->
  <div class="flex flex-wrap items-center gap-2">
    {#each selectedTags as tag (tag.id)}
      <TagPill name={tag.name} color={tag.color} onremove={() => onremove(tag.id)} />
    {/each}
    <button
      onclick={() => (isOpen = !isOpen)}
      class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-800 hover:bg-zinc-700 rounded-full transition-colors"
    >
      <Plus class="w-3 h-3" />
      Add tag
    </button>
  </div>

  <!-- Dropdown -->
  {#if isOpen}
    <div class="absolute left-0 top-full mt-2 w-64 bg-zinc-800 border border-zinc-700 rounded-lg shadow-lg z-50">
      {#if !isCreating}
        <!-- Search input -->
        <div class="p-2 border-b border-zinc-700">
          <div class="flex items-center gap-2 px-2 py-1.5 bg-zinc-900 rounded">
            <Search class="w-4 h-4 text-zinc-500" />
            <!-- svelte-ignore a11y_autofocus -->
            <input
              type="text"
              bind:value={search}
              placeholder="Search tags..."
              class="flex-1 bg-transparent text-sm text-zinc-200 placeholder-zinc-500 outline-none"
              autofocus
            />
          </div>
        </div>
      {/if}

      <!-- Tag list or create form -->
      <div class="max-h-48 overflow-y-auto">
        {#if isCreating}
          <div class="p-2 space-y-2">
            <!-- svelte-ignore a11y_autofocus -->
            <input
              type="text"
              bind:value={newTagName}
              placeholder="Tag name"
              class="w-full px-2 py-1 bg-zinc-900 text-sm text-zinc-200 placeholder-zinc-500 border border-zinc-700 rounded outline-none focus:border-amber-500"
              autofocus
              onkeydown={(e) => {
                if (e.key === 'Enter') handleCreateTag();
                if (e.key === 'Escape') { isCreating = false; createError = null; }
              }}
            />
            {#if createError}
              <p class="text-xs text-red-400">{createError}</p>
            {/if}
            <TagColorPicker selected={newTagColor} onchange={(hex) => (newTagColor = hex)} compact />
            <div class="flex gap-1.5">
              <button
                onclick={handleCreateTag}
                class="flex-1 px-2 py-1 text-xs font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
              >
                Create
              </button>
              <button
                onclick={() => { isCreating = false; newTagName = ''; newTagColor = TAG_COLORS[0].hex; createError = null; }}
                class="flex-1 px-2 py-1 text-xs font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        {:else}
          {#if filteredTags.length === 0 && search}
            <div class="p-3 text-center">
              <p class="text-sm text-zinc-500 mb-2">No tags found</p>
              <button
                onclick={() => { newTagName = search; isCreating = true; }}
                class="text-sm text-amber-500 hover:text-amber-400"
              >
                Create "{search}"
              </button>
            </div>
          {/if}
          {#each filteredTags as tag (tag.id)}
            <button
              onclick={() => { onadd(tag.id); search = ''; }}
              class="w-full px-3 py-2 flex items-center gap-2 hover:bg-zinc-700 transition-colors text-left"
            >
              <span class="w-3 h-3 rounded-full" style="background-color: {tag.color};"></span>
              <span class="text-sm text-zinc-200">{tag.name}</span>
            </button>
          {/each}
          {#if filteredTags.length > 0}
            <div class="border-t border-zinc-700">
              <button
                onclick={() => (isCreating = true)}
                class="w-full px-3 py-2 flex items-center gap-2 text-amber-500 hover:bg-zinc-700 transition-colors text-sm"
              >
                <Plus class="w-4 h-4" />
                Create new tag
              </button>
            </div>
          {/if}
          {#if filteredTags.length === 0 && !search}
            <button
              onclick={() => (isCreating = true)}
              class="w-full px-3 py-2 flex items-center gap-2 text-amber-500 hover:bg-zinc-700 transition-colors text-sm"
            >
              <Plus class="w-4 h-4" />
              Create new tag
            </button>
          {/if}
        {/if}
      </div>
    </div>
  {/if}
</div>
