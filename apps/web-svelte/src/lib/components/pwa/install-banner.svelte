<script lang="ts">
  /**
   * Banner prompting users to install the PWA.
   * Handles Chrome/Edge (beforeinstallprompt) and iOS (manual share instructions).
   */
  import { Download, X, Share } from 'lucide-svelte';
  import { browser } from '$app/environment';

  const DISMISSED_KEY = 'pwa-install-dismissed';

  let deferredPrompt = $state<Event & { prompt(): Promise<void>; userChoice: Promise<{ outcome: string }> } | null>(null);
  let isIOS = $state(false);
  let isDismissed = $state(false);

  $effect(() => {
    if (!browser) return;

    isDismissed = sessionStorage.getItem(DISMISSED_KEY) !== null;

    // Detect iOS
    isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !('MSStream' in window);

    // Listen for Chrome/Edge install prompt
    const handler = (e: Event) => {
      e.preventDefault();
      deferredPrompt = e as typeof deferredPrompt;
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  });

  const canInstall = $derived(deferredPrompt !== null);
  const visible = $derived(!isDismissed && (canInstall || isIOS));

  function handleDismiss() {
    isDismissed = true;
    if (browser) sessionStorage.setItem(DISMISSED_KEY, 'true');
  }

  async function handleInstall() {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    handleDismiss();
  }
</script>

{#if visible}
  <div class="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-sidebar p-4 shadow-lg lg:left-64">
    <div class="mx-auto flex max-w-4xl items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
          <Download class="h-5 w-5 text-accent" />
        </div>
        <div class="flex-1">
          <p class="text-sm font-semibold text-foreground">Install NotesApp</p>
          <p class="text-xs text-muted">
            {isIOS ? 'Tap Share button, then "Add to Home Screen"' : 'Install for offline access and faster performance'}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        {#if canInstall}
          <button
            type="button"
            onclick={handleInstall}
            class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-black transition-opacity hover:opacity-90"
          >
            Install
          </button>
        {/if}
        {#if isIOS}
          <div class="flex items-center gap-1 rounded-lg border border-border px-3 py-2">
            <Share class="h-4 w-4 text-accent" />
            <span class="text-xs font-medium text-accent">Share</span>
          </div>
        {/if}
        <button
          type="button"
          onclick={handleDismiss}
          class="rounded-md p-2 text-muted transition-colors hover:bg-zinc-800 hover:text-foreground"
          aria-label="Dismiss"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
{/if}
