<script lang="ts">
  /**
   * WYSIWYG editor using Tiptap with image upload support.
   * Outputs HTML content, converts to/from markdown for storage.
   */
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import Image from '@tiptap/extension-image';
  import { Table } from '@tiptap/extension-table';
  import { TableRow } from '@tiptap/extension-table-row';
  import { TableHeader } from '@tiptap/extension-table-header';
  import { TableCell } from '@tiptap/extension-table-cell';
  import Placeholder from '@tiptap/extension-placeholder';
  import { uploadNoteImage } from '$lib/services/image-upload-service';

  interface Props {
    content: string;
    onchange: (html: string) => void;
    onuploadstart?: () => void;
    onuploadend?: () => void;
    onuploaderror?: (msg: string) => void;
  }

  let { content, onchange, onuploadstart, onuploadend, onuploaderror }: Props = $props();

  let element: HTMLDivElement;
  let editorContainer: HTMLDivElement;
  let editor = $state<Editor | null>(null);

  // Pinch-to-zoom state
  let scale = $state(1);
  let initialDistance = 0;
  let isZooming = false;

  function getDistance(touches: TouchList): number {
    const [t1, t2] = [touches[0], touches[1]];
    return Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
  }

  function handleTouchStart(e: TouchEvent) {
    if (e.touches.length === 2) {
      isZooming = true;
      initialDistance = getDistance(e.touches);
    }
  }

  function handleTouchMove(e: TouchEvent) {
    if (e.touches.length === 2 && isZooming) {
      const currentDistance = getDistance(e.touches);
      const newScale = Math.min(3, Math.max(0.5, currentDistance / initialDistance));
      scale = newScale;
    }
  }

  function handleTouchEnd() {
    if (isZooming) {
      isZooming = false;
      // Animate back to scale 1
      scale = 1;
    }
  }

  onMount(() => {
    editor = new Editor({
      element,
      extensions: [
        StarterKit,
        Image.configure({ inline: true, allowBase64: false }),
        Table.configure({ resizable: false }),
        TableRow,
        TableHeader,
        TableCell,
        Placeholder.configure({ placeholder: 'Start writing...' }),
      ],
      content,
      onTransaction: () => {
        // Force Svelte reactivity on editor state change
        editor = editor;
      },
      onUpdate: ({ editor: e }) => {
        onchange(e.getHTML());
      },
      editorProps: {
        handleDrop: (view, event, slice, moved) => {
          if (moved || !event.dataTransfer) return false;
          const files = Array.from(event.dataTransfer.files).filter(f => f.type.startsWith('image/'));
          if (files.length === 0) return false;
          event.preventDefault();
          files.forEach(file => handleImageUpload(file));
          return true;
        },
        handlePaste: (view, event) => {
          const items = event.clipboardData?.items;
          if (!items) return false;
          for (const item of items) {
            if (item.type.startsWith('image/')) {
              const file = item.getAsFile();
              if (file) {
                event.preventDefault();
                handleImageUpload(file);
                return true;
              }
            }
          }
          return false;
        },
      },
    });
  });

  onDestroy(() => {
    editor?.destroy();
  });

  // Sync content from parent
  $effect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, { emitUpdate: false });
    }
  });

  async function handleImageUpload(file: File) {
    if (!editor) return;
    onuploadstart?.();
    try {
      const result = await uploadNoteImage(file);
      editor.chain().focus().setImage({ src: result.url, alt: file.name }).run();
    } catch (err) {
      onuploaderror?.(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      onuploadend?.();
    }
  }

  function insertImage() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = () => {
      const file = input.files?.[0];
      if (file) handleImageUpload(file);
    };
    input.click();
  }
</script>

<div class="wysiwyg-editor">
  <!-- Toolbar -->
  <div class="flex items-center gap-1 px-2 py-1 border-b border-border/30 bg-sidebar/50">
    <button type="button" onclick={() => editor?.chain().focus().toggleBold().run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('bold') ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Bold">
      <strong>B</strong>
    </button>
    <button type="button" onclick={() => editor?.chain().focus().toggleItalic().run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('italic') ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Italic">
      <em>I</em>
    </button>
    <button type="button" onclick={() => editor?.chain().focus().toggleStrike().run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('strike') ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Strikethrough">
      <s>S</s>
    </button>
    <span class="w-px h-4 bg-border/50 mx-1"></span>
    <button type="button" onclick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('heading', { level: 1 }) ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Heading 1">
      H1
    </button>
    <button type="button" onclick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('heading', { level: 2 }) ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Heading 2">
      H2
    </button>
    <span class="w-px h-4 bg-border/50 mx-1"></span>
    <button type="button" onclick={() => editor?.chain().focus().toggleBulletList().run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('bulletList') ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Bullet List">
      •
    </button>
    <button type="button" onclick={() => editor?.chain().focus().toggleOrderedList().run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('orderedList') ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Numbered List">
      1.
    </button>
    <button type="button" onclick={() => editor?.chain().focus().toggleCodeBlock().run()}
      class="p-1.5 rounded hover:bg-accent/10 {editor?.isActive('codeBlock') ? 'bg-accent/20 text-accent' : 'text-muted'}" title="Code Block">
      {"</>"}
    </button>
    <span class="w-px h-4 bg-border/50 mx-1"></span>
    <button type="button" onclick={insertImage}
      class="p-1.5 rounded hover:bg-accent/10 text-muted" title="Insert Image">
      🖼
    </button>
  </div>

  <!-- Editor with pinch-to-zoom -->
  <div
    bind:this={editorContainer}
    class="editor-container"
    ontouchstart={handleTouchStart}
    ontouchmove={handleTouchMove}
    ontouchend={handleTouchEnd}
    style="transform: scale({scale}); transform-origin: center; transition: {isZooming ? 'none' : 'transform 0.2s ease-out'};"
  >
    <div bind:this={element}></div>
  </div>
</div>

<style>
  .wysiwyg-editor {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  .editor-container {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
  }
  .wysiwyg-editor :global(.ProseMirror) {
    outline: none;
    min-height: 100%;
    padding: 1rem;
    line-height: 1.7;
  }
  .wysiwyg-editor :global(.ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    color: var(--muted);
    pointer-events: none;
    float: left;
    height: 0;
  }
  /* Headings */
  .wysiwyg-editor :global(.ProseMirror h1) { font-size: 2em; font-weight: bold; margin: 0.67em 0; line-height: 1.3; }
  .wysiwyg-editor :global(.ProseMirror h2) { font-size: 1.5em; font-weight: bold; margin: 0.75em 0; line-height: 1.3; }
  .wysiwyg-editor :global(.ProseMirror h3) { font-size: 1.25em; font-weight: bold; margin: 0.75em 0; line-height: 1.4; }
  .wysiwyg-editor :global(.ProseMirror h4) { font-size: 1.1em; font-weight: 600; margin: 0.75em 0; }
  /* Lists */
  .wysiwyg-editor :global(.ProseMirror ul) { list-style: disc; padding-left: 1.5em; margin: 0.5em 0; }
  .wysiwyg-editor :global(.ProseMirror ol) { list-style: decimal; padding-left: 1.5em; margin: 0.5em 0; }
  .wysiwyg-editor :global(.ProseMirror li) { margin: 0.25em 0; }
  .wysiwyg-editor :global(.ProseMirror li > ul),
  .wysiwyg-editor :global(.ProseMirror li > ol) { margin: 0.25em 0; }
  /* Inline code */
  .wysiwyg-editor :global(.ProseMirror code) {
    background: var(--sidebar);
    padding: 0.2em 0.4em;
    border-radius: 0.25rem;
    font-family: var(--font-mono);
    font-size: 0.875em;
  }
  /* Code blocks */
  .wysiwyg-editor :global(.ProseMirror pre) {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 1em;
    border-radius: 0.5rem;
    overflow-x: auto;
    margin: 0.75em 0;
    font-family: var(--font-mono);
    font-size: 0.875em;
    line-height: 1.6;
  }
  .wysiwyg-editor :global(.ProseMirror pre code) {
    background: transparent;
    padding: 0;
    font-size: inherit;
    color: inherit;
  }
  /* Blockquote */
  .wysiwyg-editor :global(.ProseMirror blockquote) {
    border-left: 3px solid var(--accent);
    padding-left: 1em;
    margin: 0.75em 0;
    color: var(--muted);
    font-style: italic;
  }
  /* Images */
  .wysiwyg-editor :global(.ProseMirror img) { max-width: 100%; height: auto; border-radius: 0.5rem; margin: 0.5em 0; }
  /* Paragraphs */
  .wysiwyg-editor :global(.ProseMirror p) { margin: 0.5em 0; }
  /* Horizontal rule */
  .wysiwyg-editor :global(.ProseMirror hr) { border: none; border-top: 1px solid var(--border); margin: 1.5em 0; }
  /* Tables */
  .wysiwyg-editor :global(.ProseMirror table) { width: 100%; border-collapse: collapse; margin: 0.75em 0; }
  .wysiwyg-editor :global(.ProseMirror th),
  .wysiwyg-editor :global(.ProseMirror td) { border: 1px solid var(--border); padding: 0.5em 0.75em; text-align: left; }
  .wysiwyg-editor :global(.ProseMirror th) { background: var(--sidebar); font-weight: 600; }
  /* Links */
  .wysiwyg-editor :global(.ProseMirror a) { color: var(--accent); text-decoration: underline; }
  /* Strong / emphasis */
  .wysiwyg-editor :global(.ProseMirror strong) { font-weight: 700; }
  .wysiwyg-editor :global(.ProseMirror em) { font-style: italic; }
  .wysiwyg-editor :global(.ProseMirror s) { text-decoration: line-through; }
</style>
