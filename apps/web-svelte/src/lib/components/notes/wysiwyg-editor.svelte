<script lang="ts">
  /**
   * WYSIWYG editor using Tiptap with image upload support.
   * Outputs HTML content, converts to/from markdown for storage.
   */
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import Image from '@tiptap/extension-image';
  import Placeholder from '@tiptap/extension-placeholder';
  import { uploadNoteImage } from '$lib/services/image-upload-service';

  interface Props {
    content: string;
    onchange: (html: string) => void;
    onuploadstart?: () => void;
    onuploaderror?: (msg: string) => void;
  }

  let { content, onchange, onuploadstart, onuploaderror }: Props = $props();

  let element: HTMLDivElement;
  let editor = $state<Editor | null>(null);

  onMount(() => {
    editor = new Editor({
      element,
      extensions: [
        StarterKit,
        Image.configure({ inline: true, allowBase64: false }),
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

  <!-- Editor -->
  <div bind:this={element} class="prose prose-sm max-w-none p-4 min-h-[200px] focus:outline-none"></div>
</div>

<style>
  .wysiwyg-editor :global(.ProseMirror) {
    outline: none;
    min-height: 200px;
  }
  .wysiwyg-editor :global(.ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    color: var(--muted);
    pointer-events: none;
    float: left;
    height: 0;
  }
  .wysiwyg-editor :global(.ProseMirror img) {
    max-width: 100%;
    height: auto;
    border-radius: 0.375rem;
  }
</style>
