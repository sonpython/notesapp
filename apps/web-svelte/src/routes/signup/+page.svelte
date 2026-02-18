<script lang="ts">
	import { goto } from '$app/navigation';
	import { Fingerprint } from 'lucide-svelte';
	import { registerPasskey, isPasskeySupported } from '$lib/auth-api';

	let displayName = $state('');
	let error = $state<string | null>(null);
	let loading = $state(false);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = null;

		const trimmedName = displayName.trim();
		if (!trimmedName) {
			error = 'Please enter your name.';
			return;
		}

		if (!isPasskeySupported()) {
			error = 'Your browser does not support passkeys. Please use a modern browser.';
			return;
		}

		loading = true;
		try {
			await registerPasskey(trimmedName);
			goto('/notes');
		} catch (err) {
			if (err instanceof Error) {
				if (err.name === 'NotAllowedError') {
					error = 'Passkey creation was cancelled. Please try again.';
				} else {
					error = err.message;
				}
			} else {
				error = 'Registration failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Create Account - NotesApp</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-background px-4">
	<div class="w-full max-w-sm">
		<div class="mb-8 text-center">
			<h1 class="text-2xl font-bold text-foreground">Create your account</h1>
			<p class="mt-2 text-sm text-muted">Set up a passkey to secure your account.</p>
		</div>

		{#if error}
			<div
				class="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
			>
				{error}
			</div>
		{/if}

		<form onsubmit={handleSubmit} class="space-y-4">
			<div>
				<label for="displayName" class="mb-1.5 block text-sm font-medium text-foreground">
					Your name
				</label>
				<input
					id="displayName"
					type="text"
					bind:value={displayName}
					required
					autocomplete="name"
					placeholder="Enter your name"
					class="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
				/>
			</div>

			<button
				type="submit"
				disabled={loading}
				class="flex h-12 w-full items-center justify-center gap-3 rounded-lg bg-accent text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
			>
				<Fingerprint class="h-5 w-5" />
				{loading ? 'Creating account...' : 'Create account with passkey'}
			</button>
		</form>

		<p class="mt-4 text-center text-xs text-muted">
			Your device will create a secure passkey using Face ID, Touch ID, or your device PIN.
		</p>

		<p class="mt-6 text-center text-sm text-muted">
			Already have an account?
			<a href="/login" class="font-medium text-accent hover:underline">Sign in</a>
		</p>
	</div>
</div>
