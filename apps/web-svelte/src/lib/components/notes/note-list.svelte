<script lang="ts">
  import { Image, Pin, Share2, Loader2 } from 'lucide-svelte';
  import { formatDistanceToNow } from 'date-fns';
  import type { Note } from '$lib/types';
  import TagPill from '$lib/components/tags/tag-pill.svelte';

  interface Props {
    notes: Note[];
    selectedId: string | null;
    onselect: (id: string) => void;
    onmoveNote?: (noteId: string, folderId: string | null) => Promise<void>;
    onLoadMore?: () => Promise<void>;
    hasMore?: boolean;
    loading?: boolean;
  }

  let { notes, selectedId, onselect, onmoveNote, onLoadMore, hasMore = false, loading = false }: Props = $props();

  let listContainer = $state<HTMLDivElement | null>(null);

  /** Strip HTML tags from text. */
  function stripHtml(text: string): string {
    return text.replace(/<[^>]*>/g, '').trim();
  }

  /** Check if content contains images. */
  function hasImages(content: string): boolean {
    return /<img\s/i.test(content) || /!\[.*?\]\(.*?\)/.test(content);
  }

  /** Extracts the first non-empty line of content as a preview snippet. */
  function getContentPreview(content: string): string {
    // Strip HTML tags for WYSIWYG content
    const stripped = stripHtml(content).replace(/\s+/g, ' ');
    const firstLine = stripped
      .split('\n')
      .map((line) => line.replace(/^#+\s*/, '').trim())
      .find((line) => line.length > 0);
    if (!firstLine) return 'No additional text';
    return firstLine.length > 80 ? firstLine.slice(0, 80) + '...' : firstLine;
  }

  /** Formats a date string as a relative time (e.g. "2 hours ago"). */
  function formatDate(dateString: string): string {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return '';
    }
  }

  const sortedNotes = $derived(
    [...notes].sort((a, b) => {
      if (a.is_pinned && !b.is_pinned) return -1;
      if (!a.is_pinned && b.is_pinned) return 1;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    })
  );

  function handleDragStart(e: DragEvent, noteId: string) {
    e.dataTransfer?.setData('noteId', noteId);
    if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move';
  }

  /** Handle scroll for lazy loading. */
  function handleScroll(e: Event) {
    if (!onLoadMore || !hasMore || loading) return;
    const target = e.target as HTMLDivElement;
    const nearBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 200;
    if (nearBottom) {
      onLoadMore();
    }
  }

  /** Handle keyboard navigation. */
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    e.preventDefault();

    const currentIndex = sortedNotes.findIndex((n) => n.id === selectedId);
    let newIndex: number;

    if (e.key === 'ArrowUp') {
      newIndex = currentIndex <= 0 ? sortedNotes.length - 1 : currentIndex - 1;
    } else {
      newIndex = currentIndex >= sortedNotes.length - 1 ? 0 : currentIndex + 1;
    }

    const newNote = sortedNotes[newIndex];
    if (newNote) {
      onselect(newNote.id);
      // Scroll into view
      const button = listContainer?.querySelector(`[data-note-id="${newNote.id}"]`);
      button?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }
</script>

{#if !sortedNotes?.length}
  <div class="flex items-center justify-center h-full text-muted text-sm">No notes yet</div>
{:else}
  <div
    bind:this={listContainer}
    class="overflow-y-auto h-full focus:outline-none"
    onscroll={handleScroll}
    onkeydown={handleKeyDown}
    tabindex="0"
    role="listbox"
    aria-label="Notes list"
  >
    {#each sortedNotes as note (note.id)}
      {@const isSelected = note.id === selectedId}
      <button
        data-note-id={note.id}
        onclick={() => onselect(note.id)}
        draggable={!!onmoveNote}
        ondragstart={(e) => handleDragStart(e, note.id)}
        role="option"
        aria-selected={isSelected}
        class="w-full text-left px-4 py-3 border-b border-border transition-colors cursor-pointer
          {isSelected
            ? 'bg-accent/10 border-l-2 border-l-accent'
            : 'hover:bg-sidebar border-l-2 border-l-transparent'}"
      >
        <div class="flex items-center gap-1.5 mb-1">
          {#if hasImages(note.content)}
            <Image class="w-3 h-3 text-emerald-500 shrink-0" />
          {/if}
          {#if note.is_shared}
            <Share2 class="w-3 h-3 text-blue-500 shrink-0" />
          {/if}
          {#if note.is_pinned}
            <Pin class="w-3 h-3 text-accent shrink-0" />
          {/if}
          <span class="font-medium text-sm text-foreground truncate">{stripHtml(note.title) || 'Untitled'}</span>
        </div>
        <p class="text-xs text-muted truncate mb-1">{getContentPreview(note.content)}</p>
        {#if note.tags && note.tags.length > 0}
          <div class="flex flex-wrap gap-1 mb-1">
            {#each note.tags.slice(0, 3) as tag (tag.id)}
              <TagPill name={tag.name} color={tag.color} size="sm" />
            {/each}
            {#if note.tags.length > 3}
              <span class="text-[10px] text-muted/70">+{note.tags.length - 3} more</span>
            {/if}
          </div>
        {/if}
        <span class="text-[11px] text-muted/70">{formatDate(note.updated_at)}</span>
      </button>
    {/each}
    {#if loading}
      <div class="flex justify-center py-4">
        <Loader2 class="w-5 h-5 text-muted animate-spin" />
      </div>
    {/if}
  </div>
{/if}
