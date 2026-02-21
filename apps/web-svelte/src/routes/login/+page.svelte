<script lang="ts">
	import { goto } from '$app/navigation';
	import { Fingerprint } from 'lucide-svelte';
	import { loginPasskey, isPasskeySupported } from '$lib/auth-api';

	const API_URL = '';

	let error = $state<string | null>(null);
	let loading = $state(false);
	let allowRegistration = $state(true);
	let rememberMe = $state(false);

	$effect(() => {
		fetch(`${API_URL}/api/config/public`, { credentials: 'include' })
			.then((res) => res.json())
			.then((data) => {
				allowRegistration = data.allow_registration;
			})
			.catch(() => {
				// Default to true if fetch fails
				allowRegistration = true;
			});
	});

	async function handleLogin() {
		error = null;

		if (!isPasskeySupported()) {
			error = 'Your browser does not support passkeys. Please use a modern browser.';
			return;
		}

		loading = true;
		try {
			await loginPasskey(rememberMe);
			goto('/notes');
		} catch (err) {
			if (err instanceof Error) {
				if (err.name === 'NotAllowedError') {
					error = 'Passkey authentication was cancelled. Please try again.';
				} else {
					error = err.message;
				}
			} else {
				error = 'Login failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Sign In - NotesApp</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-background px-4">
	<div class="w-full max-w-sm">
		<div class="mb-8 text-center">
			<h1 class="text-2xl font-bold text-foreground">Welcome back</h1>
			<p class="mt-2 text-sm text-muted">Sign in with your passkey to continue.</p>
		</div>

		{#if error}
			<div
				class="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
			>
				{error}
			</div>
		{/if}

		<label class="mb-4 flex cursor-pointer items-center gap-2 text-sm text-muted">
			<input
				type="checkbox"
				bind:checked={rememberMe}
				class="h-4 w-4 rounded border-border bg-background accent-accent"
			/>
			<span>Keep me signed in for 30 days</span>
		</label>

		<button
			onclick={handleLogin}
			disabled={loading}
			class="flex h-12 w-full items-center justify-center gap-3 rounded-lg bg-accent text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
		>
			<Fingerprint class="h-5 w-5" />
			{loading ? 'Signing in...' : 'Sign in with passkey'}
		</button>

		<p class="mt-4 text-center text-xs text-muted">
			Your device will prompt you to authenticate using Face ID, Touch ID, or your device PIN.
		</p>

		{#if allowRegistration}
			<p class="mt-6 text-center text-sm text-muted">
				Don't have an account?
				<a href="/signup" class="font-medium text-accent hover:underline">Create one</a>
			</p>
		{/if}
	</div>
</div>
