<script lang="ts">
  /**
   * Export menu dropdown for single note or bulk export.
   * Provides markdown, PDF, and bulk ZIP export options.
   */
  import { Download, FileDown, FileText, FolderArchive } from 'lucide-svelte';
  import { PUBLIC_API_URL } from '$env/static/public';
  import type { Note } from '$lib/types';

  const API_URL = PUBLIC_API_URL || 'http://localhost:8000';

  interface Props {
    note: Note | null;
    onexportAll?: () => Promise<void>;
  }

  let { note, onexportAll }: Props = $props();

  let isOpen = $state(false);
  let isExporting = $state(false);

  async function downloadBlob(url: string, filename: string) {
    const response = await fetch(url, { credentials: 'include' });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Export failed: ${response.status} - ${errorText}`);
    }
    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(objectUrl);
    document.body.removeChild(a);
  }

  async function handleExportMarkdown() {
    if (!note) return;
    isExporting = true;
    try {
      await downloadBlob(`${API_URL}/api/notes/${note.id}/export/md`, `${note.title || 'untitled'}.md`);
      isOpen = false;
    } catch (err) {
      console.error('Markdown export failed:', err);
      alert(err instanceof Error ? err.message : 'Failed to export markdown');
    } finally {
      isExporting = false;
    }
  }

  async function handleExportPdf() {
    if (!note) return;
    isExporting = true;
    try {
      await downloadBlob(`${API_URL}/api/notes/${note.id}/export/pdf`, `${note.title || 'untitled'}.pdf`);
      isOpen = false;
    } catch (err) {
      console.error('PDF export failed:', err);
      alert(err instanceof Error ? err.message : 'Failed to export PDF');
    } finally {
      isExporting = false;
    }
  }

  async function handleExportAllZip() {
    if (!onexportAll) return;
    isExporting = true;
    try {
      await onexportAll();
      isOpen = false;
    } catch (err) {
      console.error('Bulk export failed:', err);
      alert('Failed to export all notes');
    } finally {
      isExporting = false;
    }
  }
</script>

<div class="relative">
  <button
    onclick={() => (isOpen = !isOpen)}
    disabled={isExporting}
    class="p-1.5 rounded-md transition-colors cursor-pointer text-muted hover:text-foreground hover:bg-sidebar disabled:opacity-50"
    title="Export"
  >
    <Download class="w-4 h-4" />
  </button>

  {#if isOpen}
    <!-- Backdrop -->
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="fixed inset-0 z-10" role="presentation" onclick={() => (isOpen = false)}></div>

    <!-- Dropdown menu -->
    <div class="absolute right-0 top-full mt-1 w-48 bg-background border border-border rounded-md shadow-lg z-20 py-1">
      {#if note}
        <button
          onclick={handleExportMarkdown}
          disabled={isExporting}
          class="w-full text-left px-3 py-2 text-sm hover:bg-sidebar flex items-center gap-2 text-foreground disabled:opacity-50"
        >
          <FileText class="w-4 h-4" />
          Export as Markdown
        </button>
        <button
          onclick={handleExportPdf}
          disabled={isExporting}
          class="w-full text-left px-3 py-2 text-sm hover:bg-sidebar flex items-center gap-2 text-foreground disabled:opacity-50"
        >
          <FileDown class="w-4 h-4" />
          Export as PDF
        </button>
        {#if onexportAll}
          <div class="border-t border-border my-1"></div>
        {/if}
      {/if}
      {#if onexportAll}
        <button
          onclick={handleExportAllZip}
          disabled={isExporting}
          class="w-full text-left px-3 py-2 text-sm hover:bg-sidebar flex items-center gap-2 text-foreground disabled:opacity-50"
        >
          <FolderArchive class="w-4 h-4" />
          Export All as ZIP
        </button>
      {/if}
    </div>
  {/if}
</div>
