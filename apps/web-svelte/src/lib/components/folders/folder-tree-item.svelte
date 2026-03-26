<script lang="ts">
  import { ChevronRight, ChevronDown, FolderIcon, FolderOpen } from 'lucide-svelte';
  import type { Folder } from '$lib/types';
  import type { NoteCounts } from '$lib/stores/notes-store.svelte';
  import FolderContextMenu from './folder-context-menu.svelte';
  import FolderTreeItemSelf from './folder-tree-item.svelte';

  interface Props {
    folder: Folder;
    depth: number;
    selectedFolderId: string | null;
    noteCounts?: NoteCounts | null;
    onselect: (id: string, name?: string) => void;
    onrename: (id: string, name: string) => Promise<Folder>;
    ondelete: (id: string, cascade: boolean) => Promise<void>;
    oncreate: (name: string, parentId: string) => Promise<Folder>;
    onmoveNote?: (noteId: string, folderId: string | null) => Promise<void>;
  }

  let { folder, depth, selectedFolderId, noteCounts, onselect, onrename, ondelete, oncreate, onmoveNote }: Props = $props();

  // Get count for this folder
  const folderCount = $derived(noteCounts?.by_folder[folder.id] ?? 0);

  let isExpanded = $state(false);
  let showMenu = $state(false);
  let isDragOver = $state(false);

  // Rename state — renameName is populated when editing starts, not at init
  let isRenaming = $state(false);
  let renameName = $state('');
  let renameInput = $state<HTMLInputElement | null>(null);

  // Create child state
  let isCreating = $state(false);
  let createName = $state('');
  let createInput = $state<HTMLInputElement | null>(null);

  const hasChildren = $derived(folder.children && folder.children.length > 0);
  const isSelected = $derived(folder.id === selectedFolderId);
  // Increase indent for child folders: base 8px + 20px per depth level
  const paddingLeft = $derived(8 + depth * 20);

  // Focus rename input when renaming starts
  $effect(() => {
    if (isRenaming && renameInput) {
      renameInput.focus();
      renameInput.select();
    }
  });

  // Focus create input when creating starts
  $effect(() => {
    if (isCreating && createInput) {
      createInput.focus();
    }
  });

  async function submitRename() {
    const trimmed = renameName.trim();
    if (trimmed && trimmed !== folder.name) {
      try {
        await onrename(folder.id, trimmed);
      } catch {
        renameName = folder.name;
      }
    }
    isRenaming = false;
  }

  function handleRenameKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') submitRename();
    else if (e.key === 'Escape') { renameName = folder.name; isRenaming = false; }
  }

  async function submitCreate() {
    const trimmed = createName.trim();
    if (trimmed) {
      try {
        await oncreate(trimmed, folder.id);
        createName = '';
        isCreating = false;
        isExpanded = true;
      } catch { /* error handled in parent */ }
    }
  }

  function handleCreateKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') submitCreate();
    else if (e.key === 'Escape') { createName = ''; isCreating = false; }
  }

  let showDeleteDialog = $state(false);
  let cascadeDelete = $state(false);

  async function handleDelete() {
    showDeleteDialog = true;
    cascadeDelete = false;
  }

  async function confirmDelete() {
    showDeleteDialog = false;
    await ondelete(folder.id, cascadeDelete);
  }

  function handleDragOver(e: DragEvent) {
    if (!onmoveNote) return;
    e.preventDefault();
    e.stopPropagation();
    isDragOver = true;
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    isDragOver = false;
  }

  async function handleDrop(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    isDragOver = false;
    if (!onmoveNote) return;
    const noteId = e.dataTransfer?.getData('noteId');
    if (noteId) {
      try { await onmoveNote(noteId, folder.id); } catch (err) { console.error('Failed to move note:', err); }
    }
  }
</script>

<div>
  <!-- Folder row -->
  <div
    style="padding-left: {paddingLeft}px"
    class="group flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors cursor-pointer
      {isSelected ? 'bg-zinc-700/60 text-white' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'}
      {isDragOver ? 'ring-2 ring-yellow-500 bg-zinc-800' : ''}"
    onclick={() => onselect(folder.id, folder.name)}
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === 'Enter' && onselect(folder.id, folder.name)}
  >
    {#if hasChildren}
      <button
        type="button"
        onclick={(e) => { e.stopPropagation(); isExpanded = !isExpanded; }}
        class="shrink-0 p-0.5 rounded hover:bg-zinc-700/50"
      >
        {#if isExpanded}
          <ChevronDown class="h-3.5 w-3.5" />
        {:else}
          <ChevronRight class="h-3.5 w-3.5" />
        {/if}
      </button>
    {:else}
      <!-- Spacer to align with folders that have chevrons -->
      <span class="w-4 shrink-0"></span>
    {/if}

    <span title={folder.name}>
      {#if isExpanded && hasChildren}
        <FolderOpen class="h-4 w-4 shrink-0 text-yellow-500" />
      {:else}
        <FolderIcon class="h-4 w-4 shrink-0 text-yellow-500" />
      {/if}
    </span>

    {#if isRenaming}
      <input
        bind:this={renameInput}
        type="text"
        bind:value={renameName}
        onblur={submitRename}
        onkeydown={handleRenameKeydown}
        onclick={(e) => e.stopPropagation()}
        class="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5
          text-sm text-white outline-none focus:border-yellow-500"
      />
    {:else}
      <span class="flex-1 truncate">{folder.name}</span>
      {#if folderCount > 0}
        <span class="text-xs text-zinc-500 shrink-0">{folderCount}</span>
      {/if}
    {/if}

    <!-- Context menu (trigger + dropdown) -->
    <div class="relative">
      <FolderContextMenu
        show={showMenu}
        ontriggerclick={(e) => { e.stopPropagation(); showMenu = !showMenu; }}
        onclose={() => (showMenu = false)}
        onrename={() => { renameName = folder.name; isRenaming = true; }}
        onnewsubfolder={() => { isCreating = true; isExpanded = true; }}
        ondelete={handleDelete}
      />
    </div>
  </div>

  <!-- Recursive children -->
  {#if isExpanded && hasChildren}
    <div>
      {#each folder.children! as child (child.id)}
        <FolderTreeItemSelf
          folder={child}
          depth={depth + 1}
          {selectedFolderId}
          {noteCounts}
          onselect={onselect}
          onrename={onrename}
          ondelete={ondelete}
          oncreate={oncreate}
          onmoveNote={onmoveNote}
        />
      {/each}
    </div>
  {/if}

  <!-- Delete confirmation dialog -->
  {#if showDeleteDialog}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onclick={() => (showDeleteDialog = false)} role="dialog">
      <div class="bg-zinc-900 border border-zinc-700 rounded-xl p-5 w-80 shadow-xl" onclick={(e) => e.stopPropagation()} role="document">
        <h3 class="text-sm font-semibold text-white mb-3">Delete "{folder.name}"?</h3>
        <label class="flex items-center gap-2 text-sm text-zinc-300 mb-4 cursor-pointer">
          <input type="checkbox" bind:checked={cascadeDelete} class="rounded border-zinc-600 bg-zinc-800 text-red-500 focus:ring-red-500" />
          Also delete all notes in this folder
        </label>
        <div class="flex justify-end gap-2">
          <button type="button" onclick={() => (showDeleteDialog = false)} class="px-3 py-1.5 text-sm text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800">Cancel</button>
          <button type="button" onclick={confirmDelete} class="px-3 py-1.5 text-sm text-white bg-red-600 hover:bg-red-500 rounded-lg">Delete</button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Child folder creation input -->
  {#if isCreating}
    <div style="padding-left: {paddingLeft + 20}px" class="flex items-center gap-1.5 px-3 py-1.5">
      <span class="w-4 shrink-0"></span>
      <FolderIcon class="h-4 w-4 shrink-0 text-yellow-500" />
      <input
        bind:this={createInput}
        type="text"
        bind:value={createName}
        onblur={submitCreate}
        onkeydown={handleCreateKeydown}
        placeholder="Folder name"
        class="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5
          text-sm text-white outline-none focus:border-yellow-500 placeholder:text-zinc-500"
      />
    </div>
  {/if}
</div>
