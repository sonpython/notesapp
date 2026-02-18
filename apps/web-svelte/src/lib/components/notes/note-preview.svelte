<script lang="ts">
  /**
   * Renders markdown content with GFM support via svelte-markdown.
   */
  import SvelteMarkdown from 'svelte-markdown';

  interface Props {
    content: string;
  }

  let { content }: Props = $props();
</script>

<div class="prose prose-invert max-w-none px-1 py-2 note-preview">
  <SvelteMarkdown source={content} />
</div>

<style>
  /* Map react-markdown custom class equivalents using :global on prose children */
  .note-preview :global(h1) {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-foreground);
    margin-bottom: 1rem;
    margin-top: 1.5rem;
  }
  .note-preview :global(h1:first-child) { margin-top: 0; }
  .note-preview :global(h2) {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-foreground);
    margin-bottom: 0.75rem;
    margin-top: 1.25rem;
  }
  .note-preview :global(h3) {
    font-size: 1.125rem;
    font-weight: 500;
    color: var(--color-foreground);
    margin-bottom: 0.5rem;
    margin-top: 1rem;
  }
  .note-preview :global(p) {
    color: color-mix(in srgb, var(--color-foreground) 90%, transparent);
    margin-bottom: 0.75rem;
    line-height: 1.625;
  }
  .note-preview :global(ul) { list-style-type: disc; padding-left: 1.5rem; margin-bottom: 0.75rem; }
  .note-preview :global(ol) { list-style-type: decimal; padding-left: 1.5rem; margin-bottom: 0.75rem; }
  .note-preview :global(li) { margin-bottom: 0.25rem; }
  .note-preview :global(a) { color: var(--color-accent); text-decoration: underline; }
  .note-preview :global(a:hover) { opacity: 0.8; }
  .note-preview :global(code:not(pre code)) {
    background: var(--color-sidebar);
    border-radius: 0.25rem;
    padding: 0.125rem 0.375rem;
    font-size: 0.875rem;
    font-family: monospace;
    color: var(--color-accent);
  }
  .note-preview :global(pre) {
    background: var(--color-sidebar);
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    margin: 0.75rem 0;
  }
  .note-preview :global(pre code) {
    display: block;
    font-size: 0.875rem;
    font-family: monospace;
    color: color-mix(in srgb, var(--color-foreground) 90%, transparent);
    background: transparent;
    padding: 0;
  }
  .note-preview :global(blockquote) {
    border-left: 3px solid var(--color-accent);
    padding-left: 1rem;
    font-style: italic;
    color: var(--color-muted);
    margin: 0.75rem 0;
  }
  .note-preview :global(table) { width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.875rem; }
  .note-preview :global(th) {
    border: 1px solid var(--color-border);
    background: var(--color-sidebar);
    padding: 0.5rem 0.75rem;
    text-align: left;
    font-weight: 500;
  }
  .note-preview :global(td) { border: 1px solid var(--color-border); padding: 0.5rem 0.75rem; }
  .note-preview :global(hr) { border-color: var(--color-border); margin: 1.5rem 0; }
</style>
