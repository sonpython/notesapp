<script lang="ts">
  /**
   * Full note editor with title input, WYSIWYG editor (default),
   * markdown mode toggle, and action toolbar (pin, archive, delete).
   * Auto-saves changes after 500 ms debounce.
   * Supports drag-and-drop and paste image uploads.
   */
  import { Pin, Archive, Code, Trash2, ImageIcon } from 'lucide-svelte';
  import CodeMirror from 'svelte-codemirror-editor';
  import { markdown } from '@codemirror/lang-markdown';
  import type { Note, Tag } from '$lib/types';
  import { TagsStore } from '$lib/stores/tags-store.svelte';
  import WysiwygEditor from './wysiwyg-editor.svelte';
  import NoteExportMenu from './note-export-menu.svelte';
  import TagSelector from '$lib/components/tags/tag-selector.svelte';
  import { api } from '$lib/api';
  import { uploadNoteImage } from '$lib/services/image-upload-service';
  import { imageDropExtension } from '$lib/extensions/codemirror-image-drop-extension';
  import { marked } from 'marked';
  import TurndownService from 'turndown';

  interface Props {
    note: Note | null;
    onsave: (id: string, data: { title?: string; content?: string; is_pinned?: boolean; is_archived?: boolean }) => void;
    ondelete?: (id: string) => void;
    onexportAll?: () => Promise<void>;
  }

  let { note, onsave, ondelete, onexportAll }: Props = $props();

  const tagsStore = new TagsStore();

  let title = $state('');
  let content = $state('');
  let isMarkdownMode = $state(false); // false = WYSIWYG (default), true = markdown
  let noteTags = $state<Tag[]>([]);
  let isUploading = $state(false);
  let uploadError = $state<string | null>(null);

  // Debounce timers
  let titleTimer: ReturnType<typeof setTimeout> | null = null;
  let contentTimer: ReturnType<typeof setTimeout> | null = null;

  // Sync local state when selected note changes
  $effect(() => {
    if (note) {
      title = note.title;
      content = note.content;
      noteTags = note.tags ?? [];
    }
  });

  // Fetch tags on mount
  $effect(() => {
    tagsStore.fetchTags();
  });

  // Auto-save title with debounce
  $effect(() => {
    const t = title; // track reactive dependency
    if (!note || t === note.title) return;
    if (titleTimer) clearTimeout(titleTimer);
    titleTimer = setTimeout(() => {
      if (note) onsave(note.id, { title: t });
    }, 500);
    return () => { if (titleTimer) clearTimeout(titleTimer); };
  });

  // Auto-save content with debounce
  $effect(() => {
    const c = content; // track reactive dependency
    if (!note || c === note.content) return;
    if (contentTimer) clearTimeout(contentTimer);
    contentTimer = setTimeout(() => {
      if (note) onsave(note.id, { content: c });
    }, 500);
    return () => { if (contentTimer) clearTimeout(contentTimer); };
  });

  function handleTogglePin() {
    if (note) onsave(note.id, { is_pinned: !note.is_pinned });
  }

  function handleToggleArchive() {
    if (note) onsave(note.id, { is_archived: !note.is_archived });
  }

  function handleDelete() {
    if (note && ondelete) ondelete(note.id);
  }

  async function handleAddTag(tagId: string) {
    if (!note) return;
    // Optimistic update - find tag from allTags and add to local state
    const tagToAdd = tagsStore.tags.find((t) => t.id === tagId);
    if (tagToAdd && !noteTags.some((t) => t.id === tagId)) {
      noteTags = [...noteTags, tagToAdd];
    }
    try {
      await api.post(`/api/notes/${note.id}/tags`, { tag_ids: [tagId] });
    } catch (err) {
      // Rollback on error
      noteTags = noteTags.filter((t) => t.id !== tagId);
      console.error('Failed to add tag:', err);
    }
  }

  async function handleRemoveTag(tagId: string) {
    if (!note) return;
    // Optimistic update - remove from local state
    const removedTag = noteTags.find((t) => t.id === tagId);
    noteTags = noteTags.filter((t) => t.id !== tagId);
    try {
      await api.delete(`/api/notes/${note.id}/tags/${tagId}`);
    } catch (err) {
      // Rollback on error
      if (removedTag) noteTags = [...noteTags, removedTag];
      console.error('Failed to remove tag:', err);
    }
  }

  async function handleCreateTag(name: string, color: string) {
    try {
      return await tagsStore.createTag(name, color);
    } catch {
      return null;
    }
  }

  // Handle image upload from drag/drop/paste
  async function handleImageUpload(file: File) {
    isUploading = true;
    uploadError = null;
    try {
      const result = await uploadNoteImage(file);
      return { url: result.url };
    } finally {
      isUploading = false;
    }
  }

  function handleUploadError(message: string) {
    uploadError = message;
    // Clear error after 5 seconds
    setTimeout(() => { uploadError = null; }, 5000);
  }

  const turndown = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });

  function handleToggleMode() {
    if (isMarkdownMode) {
      // Markdown → WYSIWYG: convert markdown to HTML
      content = marked.parse(content, { async: false }) as string;
    } else {
      // WYSIWYG → Markdown: convert HTML to markdown
      content = turndown.turndown(content);
    }
    isMarkdownMode = !isMarkdownMode;
  }

  const cmExtensions = [
    markdown(),
    imageDropExtension(handleImageUpload, handleUploadError),
  ];
</script>

{#if !note}
  <div class="flex items-center justify-center h-full text-muted">
    <p class="text-lg">Select a note to start editing</p>
  </div>
{:else}
  <div class="flex flex-col h-full bg-note-bg">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-border/50 shrink-0 bg-note-toolbar">
      <div class="flex items-center gap-1">
        <button
          onclick={handleTogglePin}
          title={note.is_pinned ? 'Unpin' : 'Pin'}
          class="p-1.5 rounded-md transition-colors cursor-pointer {note.is_pinned ? 'text-accent bg-accent/10' : 'text-muted hover:text-foreground hover:bg-sidebar'}"
        >
          <Pin class="w-4 h-4" />
        </button>
        <button
          onclick={handleToggleArchive}
          title={note.is_archived ? 'Unarchive' : 'Archive'}
          class="p-1.5 rounded-md transition-colors cursor-pointer {note.is_archived ? 'text-accent bg-accent/10' : 'text-muted hover:text-foreground hover:bg-sidebar'}"
        >
          <Archive class="w-4 h-4" />
        </button>
        {#if ondelete}
          <button
            onclick={handleDelete}
            title="Delete"
            class="p-1.5 rounded-md transition-colors cursor-pointer text-muted hover:text-foreground hover:bg-sidebar"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        {/if}
      </div>
      <div class="flex items-center gap-1">
        {#if isUploading}
          <span class="text-xs text-muted animate-pulse flex items-center gap-1">
            <ImageIcon class="w-3 h-3" />
            Uploading...
          </span>
        {/if}
        <NoteExportMenu {note} onexportAll={onexportAll} />
        <button
          onclick={handleToggleMode}
          title={isMarkdownMode ? 'Switch to WYSIWYG' : 'Switch to Markdown'}
          class="p-1.5 rounded-md transition-colors cursor-pointer {isMarkdownMode ? 'text-accent bg-accent/10' : 'text-muted hover:text-foreground hover:bg-sidebar'}"
        >
          <Code class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Upload error notification -->
    {#if uploadError}
      <div class="px-4 py-2 bg-red-500/10 border-b border-red-500/20 text-red-500 text-sm">
        {uploadError}
      </div>
    {/if}

    <!-- Tags selector -->
    <div class="px-4 py-2 border-b border-border/50 bg-note-toolbar">
      <TagSelector
        selectedTags={noteTags}
        allTags={tagsStore.tags}
        onadd={handleAddTag}
        onremove={handleRemoveTag}
        oncreate={handleCreateTag}
      />
    </div>

    <!-- Title input -->
    <input
      type="text"
      bind:value={title}
      placeholder="Untitled"
      class="w-full px-4 py-3 text-2xl font-bold bg-transparent border-none outline-none text-foreground placeholder:text-muted/50"
    />

    <!-- Editor: WYSIWYG (default) or Markdown -->
    <div class="flex-1 overflow-y-auto">
      {#if isMarkdownMode}
        <div class="px-4 pb-4">
          <CodeMirror
            bind:value={content}
            extensions={cmExtensions}
            placeholder="Start writing..."
            class="min-h-full text-base"
            lineWrapping
            styles={{
              '&': { background: 'transparent', height: '100%' },
              '.cm-content': { fontFamily: 'inherit' },
              '.cm-line': { lineHeight: '1.6' },
            }}
          />
        </div>
      {:else}
        <WysiwygEditor
          {content}
          onchange={(html) => { content = html; }}
          onuploadstart={() => { isUploading = true; }}
          onuploaderror={handleUploadError}
        />
      {/if}
    </div>
  </div>
{/if}
