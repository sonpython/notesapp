<script lang="ts">
  import { ChevronRight, ChevronDown, FolderIcon, FolderOpen } from 'lucide-svelte';
  import type { TodoFolder } from '$lib/types';
  import FolderContextMenu from '$lib/components/folders/folder-context-menu.svelte';
  import TodoFolderTreeItemSelf from './todo-folder-tree-item.svelte';

  interface Props {
    folder: TodoFolder;
    depth: number;
    selectedFolderId: string | null;
    onselect: (id: string) => void;
    onrename: (id: string, name: string) => Promise<TodoFolder>;
    ondelete: (id: string) => Promise<void>;
    oncreate: (name: string, parentId: string) => Promise<TodoFolder>;
  }

  let { folder, depth, selectedFolderId, onselect, onrename, ondelete, oncreate }: Props = $props();

  let isExpanded = $state(false);
  let showMenu = $state(false);
  let isRenaming = $state(false);
  let renameName = $state('');
  let renameInput = $state<HTMLInputElement | null>(null);
  let isCreating = $state(false);
  let createName = $state('');
  let createInput = $state<HTMLInputElement | null>(null);

  const hasChildren = $derived(folder.children && folder.children.length > 0);
  const isSelected = $derived(folder.id === selectedFolderId);
  const paddingLeft = $derived(8 + depth * 20);

  $effect(() => {
    if (isRenaming && renameInput) { renameInput.focus(); renameInput.select(); }
  });
  $effect(() => {
    if (isCreating && createInput) createInput.focus();
  });

  async function submitRename() {
    const trimmed = renameName.trim();
    if (trimmed && trimmed !== folder.name) {
      try { await onrename(folder.id, trimmed); } catch { renameName = folder.name; }
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
      try { await oncreate(trimmed, folder.id); createName = ''; isCreating = false; isExpanded = true; } catch {}
    }
  }

  function handleCreateKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') submitCreate();
    else if (e.key === 'Escape') { createName = ''; isCreating = false; }
  }

  async function handleDelete() {
    if (window.confirm(`Delete "${folder.name}" and all its subfolders?`)) {
      await ondelete(folder.id);
    }
  }
</script>

<div>
  <div
    style="padding-left: {paddingLeft}px"
    class="group flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors cursor-pointer
      {isSelected ? 'bg-zinc-700/60 text-white' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'}"
    onclick={() => onselect(folder.id)}
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === 'Enter' && onselect(folder.id)}
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
      <span class="w-4 shrink-0"></span>
    {/if}

    <span title={folder.name}>
      {#if isExpanded && hasChildren}
        <FolderOpen class="h-4 w-4 shrink-0 text-amber-500" />
      {:else}
        <FolderIcon class="h-4 w-4 shrink-0 text-amber-500" />
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
          text-sm text-white outline-none focus:border-amber-500"
      />
    {:else}
      <span class="flex-1 truncate">{folder.name}</span>
    {/if}

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

  {#if isExpanded && hasChildren}
    <div>
      {#each folder.children! as child (child.id)}
        <TodoFolderTreeItemSelf
          folder={child}
          depth={depth + 1}
          {selectedFolderId}
          onselect={onselect}
          onrename={onrename}
          ondelete={ondelete}
          oncreate={oncreate}
        />
      {/each}
    </div>
  {/if}

  {#if isCreating}
    <div style="padding-left: {paddingLeft + 20}px" class="flex items-center gap-1.5 px-3 py-1.5">
      <span class="w-4 shrink-0"></span>
      <FolderIcon class="h-4 w-4 shrink-0 text-amber-500" />
      <input
        bind:this={createInput}
        type="text"
        bind:value={createName}
        onblur={submitCreate}
        onkeydown={handleCreateKeydown}
        placeholder="Folder name"
        class="flex-1 bg-zinc-800 border border-zinc-600 rounded px-1.5 py-0.5
          text-sm text-white outline-none focus:border-amber-500 placeholder:text-zinc-500"
      />
    </div>
  {/if}
</div>
