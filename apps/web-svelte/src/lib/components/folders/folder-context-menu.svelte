<script lang="ts">
  import { MoreHorizontal, Pencil, FolderPlus, Trash2, Link as LinkIcon } from 'lucide-svelte';

  interface Props {
    show: boolean;
    onclose: () => void;
    onrename: () => void;
    onnewsubfolder: () => void;
    ondelete: () => void;
    /** Optional share handler -- only rendered when provided */
    onshare?: () => void;
    /** Trigger button click handler passed from parent */
    ontriggerclick: (e: MouseEvent) => void;
  }

  let { show, onclose, onrename, onnewsubfolder, ondelete, onshare, ontriggerclick }: Props = $props();

  /** Close menu on outside click */
  function handleOutsideClick(node: HTMLElement) {
    function onClick(e: MouseEvent) {
      if (!node.contains(e.target as Node)) onclose();
    }
    document.addEventListener('mousedown', onClick);
    return { destroy() { document.removeEventListener('mousedown', onClick); } };
  }
</script>

<!-- Trigger button -->
<button
  type="button"
  onclick={ontriggerclick}
  class="opacity-0 group-hover:opacity-100 shrink-0 p-0.5 rounded hover:bg-zinc-700"
>
  <MoreHorizontal class="h-3.5 w-3.5" />
</button>

<!-- Dropdown menu -->
{#if show}
  <div
    use:handleOutsideClick
    class="absolute right-0 top-full mt-1 w-40 rounded-md bg-zinc-800 border border-zinc-700
      shadow-lg z-10 py-1"
  >
    <button
      onclick={(e) => { e.stopPropagation(); onrename(); onclose(); }}
      class="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 text-left"
    >
      <Pencil class="h-3 w-3" />
      Rename
    </button>
    <button
      onclick={(e) => { e.stopPropagation(); onnewsubfolder(); onclose(); }}
      class="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 text-left"
    >
      <FolderPlus class="h-3 w-3" />
      New Subfolder
    </button>
    {#if onshare}
      <button
        onclick={(e) => { e.stopPropagation(); onshare!(); onclose(); }}
        class="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 text-left"
      >
        <LinkIcon class="h-3 w-3" />
        Share
      </button>
    {/if}
    <button
      onclick={(e) => { e.stopPropagation(); ondelete(); }}
      class="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-zinc-700 text-left"
    >
      <Trash2 class="h-3 w-3" />
      Delete
    </button>
  </div>
{/if}
