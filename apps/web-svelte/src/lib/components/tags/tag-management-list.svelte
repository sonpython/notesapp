<script lang="ts">
  import { Plus, Edit2, Trash2, Check, X } from 'lucide-svelte';
  import type { Tag } from '$lib/types';
  import TagColorPicker from './tag-color-picker.svelte';
  import { TAG_COLORS } from './tag-colors';

  interface Props {
    tags: Tag[];
    oncreate: (name: string, color: string) => Promise<Tag | null>;
    onupdate: (id: string, name: string, color: string) => Promise<Tag | null>;
    ondelete: (id: string) => Promise<boolean>;
  }

  let { tags, oncreate, onupdate, ondelete }: Props = $props();

  let isCreating = $state(false);
  let newTagName = $state('');
  let newTagColor = $state(TAG_COLORS[0].hex);
  let editingId = $state<string | null>(null);
  let editName = $state('');
  let editColor = $state('');
  let deleteConfirmId = $state<string | null>(null);

  async function handleCreate() {
    if (!newTagName.trim()) return;
    const created = await oncreate(newTagName.trim(), newTagColor);
    if (created) {
      newTagName = '';
      newTagColor = TAG_COLORS[0].hex;
      isCreating = false;
    }
  }

  async function handleUpdate(id: string) {
    if (!editName.trim()) return;
    const updated = await onupdate(id, editName.trim(), editColor);
    if (updated) editingId = null;
  }

  async function handleDelete(id: string) {
    const success = await ondelete(id);
    if (success) deleteConfirmId = null;
  }

  function startEdit(tag: Tag) {
    editingId = tag.id;
    editName = tag.name;
    editColor = tag.color;
  }

  function cancelEdit() {
    editingId = null;
    editName = '';
    editColor = '';
  }
</script>

<div class="space-y-4">
  <!-- Header with create button -->
  <div class="flex items-center justify-between">
    <h3 class="text-lg font-semibold text-zinc-200">Tags</h3>
    {#if !isCreating}
      <button
        onclick={() => (isCreating = true)}
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
      >
        <Plus class="w-4 h-4" />
        Add Tag
      </button>
    {/if}
  </div>

  <!-- Create new tag form -->
  {#if isCreating}
    <div class="p-4 bg-zinc-800 border border-zinc-700 rounded-lg space-y-3">
      <div>
        <label for="tml-new-tag-name" class="block text-sm font-medium text-zinc-400 mb-1.5">Tag name</label>
        <!-- svelte-ignore a11y_autofocus -->
        <input
          id="tml-new-tag-name"
          type="text"
          bind:value={newTagName}
          placeholder="Enter tag name"
          class="w-full px-3 py-2 bg-zinc-900 text-zinc-200 placeholder-zinc-500 border border-zinc-700 rounded outline-none focus:border-amber-500"
          autofocus
          onkeydown={(e) => {
            if (e.key === 'Enter') handleCreate();
            if (e.key === 'Escape') { isCreating = false; newTagName = ''; newTagColor = TAG_COLORS[0].hex; }
          }}
        />
      </div>
      <div>
        <p class="block text-sm font-medium text-zinc-400 mb-2">Color</p>
        <TagColorPicker selected={newTagColor} onchange={(hex) => (newTagColor = hex)} />
      </div>
      <div class="flex gap-2 pt-2">
        <button
          onclick={handleCreate}
          class="flex-1 px-4 py-2 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
        >
          Create Tag
        </button>
        <button
          onclick={() => { isCreating = false; newTagName = ''; newTagColor = TAG_COLORS[0].hex; }}
          class="flex-1 px-4 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  {/if}

  <!-- Tags list -->
  {#if !tags?.length}
    <div class="text-center py-8 text-zinc-500 text-sm">
      No tags created yet. Add your first tag to get started.
    </div>
  {:else}
    <div class="space-y-2">
      {#each tags as tag (tag.id)}
        <div class="p-3 bg-zinc-800 border border-zinc-700 rounded-lg">
          {#if editingId === tag.id}
            <!-- Edit mode -->
            <div class="space-y-3">
              <div>
                <!-- svelte-ignore a11y_autofocus -->
                <input
                  type="text"
                  bind:value={editName}
                  class="w-full px-3 py-2 bg-zinc-900 text-zinc-200 border border-zinc-700 rounded outline-none focus:border-amber-500"
                  autofocus
                  onkeydown={(e) => {
                    if (e.key === 'Enter') handleUpdate(tag.id);
                    if (e.key === 'Escape') cancelEdit();
                  }}
                />
              </div>
              <TagColorPicker selected={editColor} onchange={(hex) => (editColor = hex)} />
              <div class="flex gap-2">
                <button
                  onclick={() => handleUpdate(tag.id)}
                  class="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-zinc-900 bg-amber-500 hover:bg-amber-600 rounded transition-colors"
                >
                  <Check class="w-4 h-4" />
                  Save
                </button>
                <button
                  onclick={cancelEdit}
                  class="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                >
                  <X class="w-4 h-4" />
                  Cancel
                </button>
              </div>
            </div>
          {:else}
            <!-- View mode -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="w-4 h-4 rounded-full" style="background-color: {tag.color};"></span>
                <span class="text-sm font-medium text-zinc-200">{tag.name}</span>
              </div>
              <div class="flex items-center gap-2">
                <button
                  onclick={() => startEdit(tag)}
                  class="p-1.5 text-zinc-400 hover:text-zinc-300 hover:bg-zinc-700 rounded transition-colors"
                  title="Edit tag"
                >
                  <Edit2 class="w-4 h-4" />
                </button>
                {#if deleteConfirmId === tag.id}
                  <div class="flex items-center gap-1">
                    <span class="text-xs text-zinc-400 mr-1">Delete?</span>
                    <button
                      onclick={() => handleDelete(tag.id)}
                      class="px-2 py-1 text-xs font-medium text-red-400 hover:text-red-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                    >
                      Yes
                    </button>
                    <button
                      onclick={() => (deleteConfirmId = null)}
                      class="px-2 py-1 text-xs font-medium text-zinc-400 hover:text-zinc-300 bg-zinc-700 hover:bg-zinc-600 rounded transition-colors"
                    >
                      No
                    </button>
                  </div>
                {:else}
                  <button
                    onclick={() => (deleteConfirmId = tag.id)}
                    class="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-zinc-700 rounded transition-colors"
                    title="Delete tag"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
