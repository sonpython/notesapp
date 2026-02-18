<script lang="ts">
  import { FolderIcon, Plus, FileText } from 'lucide-svelte';
  import type { Folder } from '$lib/types';
  import FolderTreeItem from './folder-tree-item.svelte';

  interface Props {
    folders: Folder[];
    selectedFolderId: string | null;
    onselectFolder: (id: string | null) => void;
    oncreateFolder: (name: string, parentId?: string) => Promise<Folder>;
    onrenameFolder: (id: string, name: string) => Promise<Folder>;
    ondeleteFolder: (id: string) => Promise<void>;
    onmoveNote?: (noteId: string, folderId: string | null) => Promise<void>;
  }

  let {
    folders,
    selectedFolderId,
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
  <!-- "All Notes" item -->
  <button
    type="button"
    onclick={() => onselectFolder(null)}
    class="w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors text-left
      {selectedFolderId === null
        ? 'bg-zinc-700/60 text-white'
        : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'}"
  >
    <FileText class="h-4 w-4 shrink-0" />
    All Notes
  </button>

  <!-- Empty state -->
  {#if isEmpty}
    <div class="flex flex-col items-center gap-2 py-6 text-center">
      <FolderIcon class="h-8 w-8 text-zinc-700" />
      <p class="text-xs text-zinc-600">No folders yet</p>
      <button
        type="button"
        onclick={() => (isCreatingRoot = true)}
        class="flex items-center gap-1.5 rounded-md bg-zinc-800 px-3 py-1.5
          text-xs text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-zinc-300"
      >
        <Plus class="h-3 w-3" />
        New Folder
      </button>
    </div>
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
      onselect={onselectFolder}
      onrename={onrenameFolder}
      ondelete={ondeleteFolder}
      oncreate={oncreateFolder}
      {onmoveNote}
    />
  {/each}
</div>
