<script lang="ts">
  import { FolderIcon, Plus } from 'lucide-svelte';
  import type { Folder } from '$lib/types';
  import type { NoteCounts } from '$lib/stores/notes-store.svelte';
  import FolderTreeItem from './folder-tree-item.svelte';

  interface Props {
    folders: Folder[];
    selectedFolderId: string | null;
    noteCounts?: NoteCounts | null;
    onselectFolder: (id: string | null, name?: string) => void;
    oncreateFolder: (name: string, parentId?: string) => Promise<Folder>;
    onrenameFolder: (id: string, name: string) => Promise<Folder>;
    ondeleteFolder: (id: string) => Promise<void>;
    onmoveNote?: (noteId: string, folderId: string | null) => Promise<void>;
  }

  let {
    folders,
    selectedFolderId,
    noteCounts,
    onselectFolder,
    oncreateFolder,
    onrenameFolder,
    ondeleteFolder,
    onmoveNote,
  }: Props = $props();

  let isCreatingRoot = $state(false);
  let newRootName = $state('');
  let rootInput = $state<HTMLInputElement | null>(null);

  const isEmpty = $derived(!folders?.length && !isCreatingRoot);

  // Focus root input when it appears
  $effect(() => {
    if (isCreatingRoot && rootInput) rootInput.focus();
  });

  async function submitRootCreate() {
    const trimmed = newRootName.trim();
    if (trimmed) {
      try {
        await oncreateFolder(trimmed);
        newRootName = '';
        isCreatingRoot = false;
      } catch { /* error handled in parent */ }
    }
  }

  function handleRootKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') submitRootCreate();
    else if (e.key === 'Escape') { newRootName = ''; isCreatingRoot = false; }
  }
</script>

<div class="space-y-0.5">
  <!-- Folders header with New Folder button -->
  <div class="flex items-center justify-between px-3 pt-2 pb-1">
    <span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Folders</span>
    <button
      type="button"
      onclick={() => (isCreatingRoot = true)}
      class="rounded p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
      title="New Folder"
    >
      <Plus class="h-3.5 w-3.5" />
    </button>
  </div>

  <!-- Empty state -->
  {#if isEmpty}
    <p class="px-3 py-2 text-xs text-zinc-600">No folders yet</p>
  {/if}

  <!-- Root folder creation input -->
  {#if isCreatingRoot}
    <div class="flex items-center gap-1.5 px-3 py-1.5">
      <FolderIcon class="h-4 w-4 shrink-0 text-yellow-500" />
      <input
        bind:this={rootInput}
        type="text"
        bind:value={newRootName}
        onblur={submitRootCreate}
        onkeydown={handleRootKeydown}
        placeholder="Folder name"
        class="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5
          text-sm text-white outline-none focus:border-yellow-500 placeholder:text-zinc-500"
      />
    </div>
  {/if}

  <!-- Folder tree -->
  {#each folders as folder (folder.id)}
    <FolderTreeItem
      {folder}
      depth={0}
      {selectedFolderId}
      {noteCounts}
      onselect={onselectFolder}
      onrename={onrenameFolder}
      ondelete={ondeleteFolder}
      oncreate={oncreateFolder}
      {onmoveNote}
    />
  {/each}
</div>
