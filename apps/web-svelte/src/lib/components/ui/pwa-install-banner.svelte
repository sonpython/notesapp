<script lang="ts">
	/**
	 * PWA install prompt banner for mobile.
	 * Shows on first visit, dismissal = 30 day cooldown.
	 */
	import { browser } from '$app/environment';
	import { X, Download, Share } from 'lucide-svelte';

	const STORAGE_KEY = 'pwa-install-dismissed';
	const COOLDOWN_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

	let showBanner = $state(false);
	let showIOSModal = $state(false);
	let deferredPrompt: Event | null = null;

	const isIOS = browser && /iPad|iPhone|iPod/.test(navigator.userAgent);
	const isStandalone = browser && window.matchMedia('(display-mode: standalone)').matches;
	const isMobile = browser && /Mobile|Android/.test(navigator.userAgent);

	$effect(() => {
		if (!browser || !isMobile || isStandalone) return;

		// Check cooldown
		const dismissed = localStorage.getItem(STORAGE_KEY);
		if (dismissed && Date.now() - parseInt(dismissed) < COOLDOWN_MS) return;

		// Listen for install prompt (Chrome/Edge)
		window.addEventListener('beforeinstallprompt', (e) => {
			e.preventDefault();
			deferredPrompt = e;
			showBanner = true;
		});

		// iOS doesn't fire beforeinstallprompt, show banner anyway
		if (isIOS) {
			showBanner = true;
		}
	});

	async function handleInstall() {
		if (isIOS) {
			showIOSModal = true;
			return;
		}
		if (deferredPrompt) {
			(deferredPrompt as any).prompt();
			const result = await (deferredPrompt as any).userChoice;
			if (result.outcome === 'accepted') {
				showBanner = false;
			}
			deferredPrompt = null;
		}
	}

	function handleDismiss() {
		localStorage.setItem(STORAGE_KEY, Date.now().toString());
		showBanner = false;
		showIOSModal = false;
	}
</script>

{#if showBanner}
	<div class="flex items-center justify-between gap-2 bg-accent px-3 py-2 text-black text-sm">
		<div class="flex items-center gap-2">
			<Download class="h-4 w-4" />
			<span class="font-medium">Install NotesApp</span>
		</div>
		<div class="flex items-center gap-1">
			<button onclick={handleInstall} class="rounded bg-black/20 px-3 py-1 text-xs font-medium hover:bg-black/30">
				Install
			</button>
			<button onclick={handleDismiss} class="p-1 hover:bg-black/20 rounded">
				<X class="h-4 w-4" />
			</button>
		</div>
	</div>
{/if}

<!-- iOS Instructions Modal -->
{#if showIOSModal}
	<div class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4" onclick={handleDismiss}>
		<div class="w-full max-w-sm rounded-xl bg-background p-4 text-foreground" onclick={(e) => e.stopPropagation()}>
			<h3 class="mb-3 text-lg font-semibold">Add to Home Screen</h3>
			<ol class="space-y-2 text-sm text-muted">
				<li class="flex items-center gap-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-full bg-accent/20 text-xs text-accent">1</span>
					<span>Tap <Share class="inline h-4 w-4" /> Share button</span>
				</li>
				<li class="flex items-center gap-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-full bg-accent/20 text-xs text-accent">2</span>
					<span>Scroll down, tap "Add to Home Screen"</span>
				</li>
				<li class="flex items-center gap-2">
					<span class="flex h-6 w-6 items-center justify-center rounded-full bg-accent/20 text-xs text-accent">3</span>
					<span>Tap "Add" to confirm</span>
				</li>
			</ol>
			<button onclick={handleDismiss} class="mt-4 w-full rounded-lg bg-accent py-2 text-sm font-medium text-black">
				Got it
			</button>
		</div>
	</div>
{/if}
