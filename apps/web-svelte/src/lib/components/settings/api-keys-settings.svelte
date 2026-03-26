<script lang="ts">
  /**
   * API Keys management UI for Settings page.
   * Create, view, and delete API keys for MCP integration.
   * Full key shown only once at creation.
   */
  import { onMount } from 'svelte';
  import { Key, Plus, Trash2, Copy, Check, Eye, EyeOff } from 'lucide-svelte';
  import { api } from '$lib/api';

  interface ApiKeyItem {
    id: string;
    name: string;
    key_prefix: string;
    expires_at: string | null;
    last_used_at: string | null;
    created_at: string;
  }

  interface ApiKeyCreated extends ApiKeyItem {
    key: string;
  }

  let keys = $state<ApiKeyItem[]>([]);
  let loading = $state(true);
  let showCreateForm = $state(false);
  let newKeyName = $state('');
  let newKeyExpiry = $state<'never' | '30d' | '90d' | '1y' | 'custom'>('never');
  let newKeyCustomDate = $state('');
  let createdKey = $state<ApiKeyCreated | null>(null);
  let copied = $state(false);
  let showKey = $state(false);

  onMount(fetchKeys);

  async function fetchKeys() {
    loading = true;
    try {
      keys = await api.get<ApiKeyItem[]>('/api/api-keys/');
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
    }
    loading = false;
  }

  function getExpiryDate(): string | null {
    if (newKeyExpiry === 'never') return null;
    if (newKeyExpiry === 'custom') return newKeyCustomDate ? new Date(newKeyCustomDate).toISOString() : null;
    const days = { '30d': 30, '90d': 90, '1y': 365 }[newKeyExpiry];
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString();
  }

  async function handleCreate() {
    if (!newKeyName.trim()) return;
    try {
      const result = await api.post<ApiKeyCreated>('/api/api-keys/', {
        name: newKeyName.trim(),
        expires_at: getExpiryDate(),
      });
      createdKey = result;
      showCreateForm = false;
      newKeyName = '';
      newKeyExpiry = 'never';
      await fetchKeys();
    } catch (err) {
      console.error('Failed to create API key:', err);
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`Delete API key "${name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/api-keys/${id}`);
      keys = keys.filter((k) => k.id !== id);
    } catch (err) {
      console.error('Failed to delete API key:', err);
    }
  }

  async function copyKey() {
    if (!createdKey) return;
    await navigator.clipboard.writeText(createdKey.key);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h2 class="text-lg font-semibold text-foreground">API Keys</h2>
    <button
      onclick={() => { showCreateForm = true; createdKey = null; }}
      class="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-black transition-opacity hover:opacity-90"
    >
      <Plus class="h-3.5 w-3.5" /> New Key
    </button>
  </div>

  <p class="text-xs text-muted">
    API keys authenticate MCP connections from Claude Desktop and other AI agents.
  </p>

  <!-- Created key banner (shown once) -->
  {#if createdKey}
    <div class="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 space-y-3">
      <p class="text-sm font-medium text-amber-500">
        Key created! Copy it now — it won't be shown again.
      </p>
      <div class="flex items-center gap-2">
        <code class="flex-1 rounded bg-zinc-800 px-3 py-2 text-sm text-white font-mono break-all">
          {showKey ? createdKey.key : '•'.repeat(40)}
        </code>
        <button onclick={() => (showKey = !showKey)} class="p-2 text-muted hover:text-foreground" title={showKey ? 'Hide' : 'Show'}>
          {#if showKey}<EyeOff class="h-4 w-4" />{:else}<Eye class="h-4 w-4" />{/if}
        </button>
        <button onclick={copyKey} class="p-2 text-muted hover:text-foreground" title="Copy">
          {#if copied}<Check class="h-4 w-4 text-green-500" />{:else}<Copy class="h-4 w-4" />{/if}
        </button>
      </div>
      <button
        onclick={() => { createdKey = null; showKey = false; }}
        class="text-xs text-muted hover:text-foreground"
      >
        Dismiss
      </button>
    </div>
  {/if}

  <!-- Create form -->
  {#if showCreateForm}
    <div class="rounded-lg border border-border bg-sidebar p-4 space-y-3">
      <input
        type="text"
        bind:value={newKeyName}
        placeholder="Key name (e.g. Claude Desktop)"
        class="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-accent"
      />
      <div class="flex items-center gap-2">
        <label class="text-xs text-muted">Expires:</label>
        <select
          bind:value={newKeyExpiry}
          class="rounded border border-border bg-background px-2 py-1 text-sm text-foreground"
        >
          <option value="never">Never</option>
          <option value="30d">30 days</option>
          <option value="90d">90 days</option>
          <option value="1y">1 year</option>
          <option value="custom">Custom date</option>
        </select>
        {#if newKeyExpiry === 'custom'}
          <input
            type="date"
            bind:value={newKeyCustomDate}
            class="rounded border border-border bg-background px-2 py-1 text-sm text-foreground"
          />
        {/if}
      </div>
      <div class="flex gap-2">
        <button
          onclick={handleCreate}
          disabled={!newKeyName.trim()}
          class="rounded-lg bg-accent px-4 py-1.5 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          Create
        </button>
        <button
          onclick={() => { showCreateForm = false; newKeyName = ''; }}
          class="rounded-lg px-4 py-1.5 text-sm text-muted hover:text-foreground"
        >
          Cancel
        </button>
      </div>
    </div>
  {/if}

  <!-- Keys list -->
  {#if loading}
    <p class="text-sm text-muted">Loading...</p>
  {:else if keys.length === 0}
    <div class="rounded-lg border border-border bg-sidebar p-6 text-center">
      <Key class="mx-auto h-8 w-8 text-muted/50 mb-2" />
      <p class="text-sm text-muted">No API keys yet</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each keys as key (key.id)}
        <div class="flex items-center gap-3 rounded-lg border border-border bg-sidebar px-4 py-3">
          <Key class="h-4 w-4 shrink-0 text-muted" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-foreground truncate">{key.name}</p>
            <p class="text-xs text-muted">
              <code class="font-mono">{key.key_prefix}</code>
              · Created {formatDate(key.created_at)}
              {#if key.expires_at}
                · Expires {formatDate(key.expires_at)}
              {:else}
                · Never expires
              {/if}
              {#if key.last_used_at}
                · Last used {formatDate(key.last_used_at)}
              {/if}
            </p>
          </div>
          <button
            onclick={() => handleDelete(key.id, key.name)}
            class="shrink-0 rounded p-1.5 text-muted transition-colors hover:bg-red-500/10 hover:text-red-500"
            title="Delete key"
          >
            <Trash2 class="h-4 w-4" />
          </button>
        </div>
      {/each}
    </div>
  {/if}

  <!-- MCP config hint -->
  <details class="text-xs text-muted">
    <summary class="cursor-pointer hover:text-foreground">Claude Desktop configuration</summary>
    <pre class="mt-2 rounded bg-zinc-800 p-3 text-zinc-300 overflow-x-auto">{`{
  "mcpServers": {
    "notesapp-todos": {
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}`}</pre>
  </details>
</div>
