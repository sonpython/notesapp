<script lang="ts">
	import { Fingerprint, FileText, CheckSquare } from 'lucide-svelte';
</script>

<svelte:head>
	<title>NotesApp - Your Personal Notes & Tasks</title>
</svelte:head>

<main class="flex min-h-screen flex-col items-center justify-center bg-background px-4">
	<div class="w-full max-w-md text-center">
		<h1 class="text-4xl font-bold text-foreground mb-4">NotesApp</h1>
		<p class="text-muted mb-8">Your personal notes and tasks, secured with passkeys.</p>

		<div class="flex flex-col gap-4 mb-8">
			<div class="flex items-center gap-3 p-4 bg-sidebar rounded-lg border border-border">
				<FileText class="h-6 w-6 text-accent" />
				<span class="text-foreground">Organize notes in folders</span>
			</div>
			<div class="flex items-center gap-3 p-4 bg-sidebar rounded-lg border border-border">
				<CheckSquare class="h-6 w-6 text-accent" />
				<span class="text-foreground">Track todos with reminders</span>
			</div>
			<div class="flex items-center gap-3 p-4 bg-sidebar rounded-lg border border-border">
				<Fingerprint class="h-6 w-6 text-accent" />
				<span class="text-foreground">Passwordless passkey auth</span>
			</div>
		</div>

		<div class="flex flex-col gap-3">
			<a
				href="/signup"
				class="flex h-12 items-center justify-center gap-2 rounded-lg bg-accent text-black font-semibold transition-opacity hover:opacity-90"
			>
				<Fingerprint class="h-5 w-5" />
				Get Started
			</a>
			<a
				href="/login"
				class="flex h-12 items-center justify-center rounded-lg border border-border text-foreground font-medium transition-colors hover:bg-sidebar"
			>
				Sign In
			</a>
		</div>
	</div>
</main>
