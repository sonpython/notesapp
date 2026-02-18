<script lang="ts">
	import { WifiOff } from 'lucide-svelte';
</script>

<svelte:head>
	<title>Offline - NotesApp</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-background px-4">
	<div class="text-center">
		<WifiOff class="mx-auto h-16 w-16 text-muted mb-4" />
		<h1 class="text-2xl font-bold text-foreground mb-2">You're offline</h1>
		<p class="text-muted mb-6">Check your internet connection and try again.</p>
		<button
			onclick={() => window.location.reload()}
			class="px-6 py-2 bg-accent text-black font-semibold rounded-lg hover:opacity-90 transition-opacity"
		>
			Retry
		</button>
	</div>
</div>
