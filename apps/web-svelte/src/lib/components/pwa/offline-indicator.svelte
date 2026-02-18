<script lang="ts">
  /**
   * Offline status indicator – appears when network is disconnected.
   * Uses the shared online-status store (reactive $state inside class).
   */
  import { CloudOff } from 'lucide-svelte';
  import { onlineStatus } from '$lib/stores/online-status.svelte';
</script>

{#if !onlineStatus.isOnline}
  <div
    class="flex items-center gap-1.5 rounded-full border border-amber-800 bg-amber-900/30 px-3 py-1 text-xs font-medium text-amber-400 transition-all"
  >
    <CloudOff class="h-3.5 w-3.5" />
    <span>Offline</span>
  </div>
{/if}
