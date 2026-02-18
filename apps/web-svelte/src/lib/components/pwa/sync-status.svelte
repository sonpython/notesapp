<script lang="ts">
  /**
   * Sync status indicator – shows pending changes count and syncing state.
   * Polls IndexedDB sync queue every 5 s when offline.
   * TODO (Phase 3): replace polling with real sync-queue events.
   */
  import { RefreshCw, CheckCircle } from 'lucide-svelte';
  import { onlineStatus } from '$lib/stores/online-status.svelte';

  let pendingCount = $state(0);
  let isSyncing = $state(false);

  async function checkPendingChanges() {
    try {
      // Placeholder: Phase 3 will query the real sync-queue store.
      // const queue = await getAllFromSyncQueue();
      // pendingCount = queue.length;
      pendingCount = 0;
    } catch (err) {
      console.error('Failed to check sync queue:', err);
      pendingCount = 0;
    }
  }

  $effect(() => {
    checkPendingChanges();

    if (!onlineStatus.isOnline) {
      const interval = setInterval(checkPendingChanges, 5000);
      return () => clearInterval(interval);
    }
  });

  $effect(() => {
    if (onlineStatus.isOnline && pendingCount > 0) {
      const timeout = setTimeout(() => {
        isSyncing = true;
        setTimeout(() => {
          isSyncing = false;
          pendingCount = 0;
        }, 2000);
      }, 0);
      return () => clearTimeout(timeout);
    }
  });
</script>

{#if pendingCount > 0 || isSyncing}
  <div
    class="flex items-center gap-1.5 rounded-full border border-border bg-sidebar px-3 py-1 text-xs font-medium text-muted transition-all"
  >
    {#if isSyncing}
      <RefreshCw class="h-3.5 w-3.5 animate-spin text-accent" />
      <span class="text-accent">Syncing...</span>
    {:else if pendingCount > 0}
      <RefreshCw class="h-3.5 w-3.5" />
      <span>{pendingCount} {pendingCount === 1 ? 'change' : 'changes'} pending</span>
    {:else}
      <CheckCircle class="h-3.5 w-3.5 text-green-400" />
      <span class="text-green-400">All synced</span>
    {/if}
  </div>
{/if}
