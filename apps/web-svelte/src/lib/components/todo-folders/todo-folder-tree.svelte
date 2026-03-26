<script lang="ts">
  import { FolderIcon, Plus } from 'lucide-svelte';
  import type { TodoFolder } from '$lib/types';
  import TodoFolderTreeItem from './todo-folder-tree-item.svelte';

  interface Props {
    folders: TodoFolder[];
    selectedFolderId: string | null;
    onselectFolder: (id: string | null) => void;
    oncreateFolder: (name: string, parentId?: string) => Promise<TodoFolder>;
    onrenameFolder: (id: string, name: string) => Promise<TodoFolder>;
    ondeleteFolder: (id: string) => Promise<void>;
  }

  let {
    folders,
    selectedFolderId,
    onselectFolder,
    oncreateFolder,
    onrenameFolder,
    ondeleteFolder,
  }: Props = $props();

  let isCreatingRoot = $state(false);
  let newRootName = $state('');
  let rootInput = $state<HTMLInputElement | null>(null);

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
  <!-- Folders header -->
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

  {#if !folders?.length && !isCreatingRoot}
    <p class="px-3 py-2 text-xs text-zinc-600">No folders yet</p>
  {/if}

  {#if isCreatingRoot}
    <div class="flex items-center gap-1.5 px-3 py-1.5">
      <FolderIcon class="h-4 w-4 shrink-0 text-amber-500" />
      <input
        bind:this={rootInput}
        type="text"
        bind:value={newRootName}
        onblur={submitRootCreate}
        onkeydown={handleRootKeydown}
        placeholder="Folder name"
        class="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5
          text-sm text-white outline-none focus:border-amber-500 placeholder:text-zinc-500"
      />
    </div>
  {/if}

  {#each folders as folder (folder.id)}
    <TodoFolderTreeItem
      {folder}
      depth={0}
      {selectedFolderId}
      onselect={onselectFolder}
      onrename={onrenameFolder}
      ondelete={ondeleteFolder}
      oncreate={oncreateFolder}
    />
  {/each}
</div>
