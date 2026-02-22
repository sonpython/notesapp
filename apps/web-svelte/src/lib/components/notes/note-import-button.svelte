<script lang="ts">
  /**
   * Import button for .md files - creates a new note from markdown file.
   * Duplicate detection by title prevents re-importing same file.
   * Converts markdown to HTML since editor defaults to WYSIWYG mode.
   */
  import { FileUp } from 'lucide-svelte';
  import { marked } from 'marked';
  import type { Note } from '$lib/types';

  interface Props {
    existingNotes: Note[];
    onimport: (data: { title: string; content: string }) => Promise<Note | null>;
    folderId?: string | null;
    variant?: 'toolbar' | 'fab';
  }

  let { existingNotes, onimport, variant = 'toolbar' }: Props = $props();
  let fileInput: HTMLInputElement;
  let isImporting = $state(false);

  function extractTitleFromMarkdown(content: string, filename: string): string {
    // Try to extract title from first # heading
    const match = content.match(/^#\s+(.+)$/m);
    if (match) return match[1].trim();
    // Fallback to filename without extension
    return filename.replace(/\.md$/i, '');
  }

  async function hashContent(content: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  async function isDuplicate(title: string, contentHash: string): Promise<boolean> {
    const normalizedTitle = title.toLowerCase().trim();
    const matchingNote = existingNotes.find((n) => n.title.toLowerCase().trim() === normalizedTitle);
    if (!matchingNote) return false;
    // Title matches - check content hash
    const existingHash = await hashContent(matchingNote.content);
    return existingHash === contentHash;
  }

  async function handleFileSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    isImporting = true;
    try {
      const rawMarkdown = await file.text();
      const title = extractTitleFromMarkdown(rawMarkdown, file.name);

      // Convert markdown to HTML since editor defaults to WYSIWYG mode
      const htmlContent = marked.parse(rawMarkdown, { async: false }) as string;

      // Check duplicate: same title AND same content hash
      const contentHash = await hashContent(htmlContent);
      if (await isDuplicate(title, contentHash)) {
        alert(`A note with title "${title}" and identical content already exists. Import skipped.`);
        return;
      }
      const note = await onimport({ title, content: htmlContent });
      if (note) {
        // Success - no alert needed, note will appear in list
      }
    } catch (err) {
      console.error('Import failed:', err);
      alert(err instanceof Error ? err.message : 'Failed to import markdown file');
    } finally {
      isImporting = false;
      // Reset input so same file can be selected again
      input.value = '';
    }
  }

  function handleClick() {
    fileInput?.click();
  }
</script>

<input
  type="file"
  accept=".md,.markdown,text/markdown"
  bind:this={fileInput}
  onchange={handleFileSelect}
  class="hidden"
/>

{#if variant === 'fab'}
  <button
    onclick={handleClick}
    disabled={isImporting}
    aria-label="Import markdown file"
    class="flex h-11 w-11 items-center justify-center rounded-full bg-sidebar border border-border text-muted shadow-md transition-transform hover:scale-105 hover:text-foreground active:scale-95 disabled:opacity-50"
  >
    <FileUp class="h-5 w-5" />
  </button>
{:else}
  <button
    onclick={handleClick}
    disabled={isImporting}
    title="Import markdown file"
    class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-background text-muted transition-colors hover:bg-sidebar hover:text-foreground disabled:opacity-50"
  >
    <FileUp class="h-4 w-4" />
  </button>
{/if}
