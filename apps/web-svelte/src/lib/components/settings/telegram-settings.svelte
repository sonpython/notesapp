<script lang="ts">
	/**
	 * Telegram settings panel - link/unlink, backup settings, and restore.
	 */
	import { api } from '$lib/api';
	import { onMount } from 'svelte';

	interface TelegramStatus {
		is_linked: boolean;
		is_enabled: boolean;
		chat_id?: string;
		bot_linked_at?: string;
	}

	interface BackupSettings {
		backup_enabled: boolean;
		backup_schedule: 'daily' | 'weekly' | null;
		backup_retention: number;
		last_backup_at: string | null;
		next_backup_at: string | null;
	}

	interface BackupItem {
		id: string;
		telegram_file_id: string;
		backup_size_bytes: number;
		entity_counts: Record<string, number>;
		version_number: number;
		created_at: string;
	}

	let status = $state<TelegramStatus | null>(null);
	let linkCode = $state<string | null>(null);
	let backupSettings = $state<BackupSettings | null>(null);
	let backups = $state<BackupItem[]>([]);
	let loading = $state(true);
	let actionLoading = $state(false);
	let error = $state<string | null>(null);

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			status = await api.get<TelegramStatus>('/api/telegram/status');
			if (status.is_linked) {
				[backupSettings, { items: backups }] = await Promise.all([
					api.get<BackupSettings>('/api/backup/settings'),
					api.get<{ items: BackupItem[] }>('/api/backup/list')
				]);
			}
		} catch (e) {
			error = 'Failed to load settings';
		} finally {
			loading = false;
		}
	}

	async function handleLink() {
		actionLoading = true;
		try {
			const res = await api.post<{ link_code: string; bot_username: string }>('/api/telegram/link');
			linkCode = res.link_code;
		} catch {
			error = 'Failed to generate link code';
		} finally {
			actionLoading = false;
		}
	}

	async function handleUnlink() {
		if (!confirm('Unlink Telegram? You will stop receiving reminders.')) return;
		actionLoading = true;
		try {
			await api.post('/api/telegram/unlink');
			status = { is_linked: false, is_enabled: false };
			backupSettings = null;
			backups = [];
			linkCode = null;
		} catch {
			error = 'Failed to unlink';
		} finally {
			actionLoading = false;
		}
	}

	async function updateBackupSettings(updates: Partial<BackupSettings>) {
		actionLoading = true;
		try {
			backupSettings = await api.put<BackupSettings>('/api/backup/settings', updates);
		} catch {
			error = 'Failed to update settings';
		} finally {
			actionLoading = false;
		}
	}

	async function triggerBackup() {
		actionLoading = true;
		error = null;
		try {
			await api.post('/api/backup/trigger');
			// Reload backups list
			const res = await api.get<{ items: BackupItem[] }>('/api/backup/list');
			backups = res.items;
			backupSettings = await api.get<BackupSettings>('/api/backup/settings');
		} catch {
			error = 'Backup failed (rate limit: 1/hour)';
		} finally {
			actionLoading = false;
		}
	}

	async function restoreBackup(backupId: string) {
		if (!confirm('Restore this backup? Your current data will be merged.')) return;
		actionLoading = true;
		error = null;
		try {
			await api.post(`/api/backup/${backupId}/restore`);
			alert('Restore complete! Refresh the page to see changes.');
		} catch {
			error = 'Restore failed (rate limit: 1/hour)';
		} finally {
			actionLoading = false;
		}
	}

	function formatBytes(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleString();
	}
</script>

<div class="space-y-6">
	<h2 class="text-lg font-semibold text-foreground">Telegram</h2>

	{#if loading}
		<p class="text-sm text-muted">Loading...</p>
	{:else if error}
		<p class="text-sm text-red-500">{error}</p>
	{:else if !status?.is_linked}
		<!-- Not linked - show link flow -->
		<div class="rounded-lg border border-border bg-sidebar p-4 space-y-3">
			<p class="text-sm text-muted">Link your Telegram to receive reminders and backup data.</p>
			<p class="text-sm">
				Chat với bot: <a href="https://t.me/notesappx_bot" target="_blank" class="text-accent hover:underline">@NotesAppX</a>
			</p>
			{#if linkCode}
				<div class="rounded bg-accent/10 p-3">
					<p class="text-xs text-muted mb-1">Gửi lệnh này cho bot:</p>
					<div class="flex items-center gap-2">
						<code class="text-lg font-mono text-accent">/start {linkCode}</code>
						<button
							onclick={() => { navigator.clipboard.writeText(`/start ${linkCode}`); }}
							class="p-1 rounded hover:bg-accent/20 text-muted hover:text-accent"
							title="Copy"
						>
							<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
						</button>
					</div>
				</div>
				<p class="text-xs text-muted">Bot sẽ phản hồi khi link thành công.</p>
				<button onclick={loadData} class="text-xs text-accent hover:underline">
					Đã link xong → Refresh
				</button>
			{:else}
				<button
					onclick={handleLink}
					disabled={actionLoading}
					class="rounded-lg bg-accent px-4 py-2 text-sm text-white hover:bg-accent/90 disabled:opacity-50"
				>
					{actionLoading ? 'Loading...' : 'Tạo mã liên kết'}
				</button>
			{/if}
		</div>
	{:else}
		<!-- Linked - show settings -->
		<div class="space-y-4">
			<!-- Status -->
			<div class="rounded-lg border border-border bg-sidebar p-4">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-foreground">✅ Telegram Linked</p>
						<p class="text-xs text-muted">
							Since {status.bot_linked_at ? formatDate(status.bot_linked_at) : 'N/A'}
						</p>
					</div>
					<button
						onclick={handleUnlink}
						disabled={actionLoading}
						class="text-xs text-red-500 hover:underline"
					>
						Unlink
					</button>
				</div>
			</div>

			<!-- Backup Settings -->
			{#if backupSettings}
				<div class="rounded-lg border border-border bg-sidebar p-4 space-y-3">
					<h3 class="text-sm font-medium text-foreground">Backup Settings</h3>

					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							checked={backupSettings.backup_enabled}
							onchange={(e) => updateBackupSettings({ backup_enabled: e.currentTarget.checked })}
							class="rounded"
						/>
						<span class="text-sm text-foreground">Enable auto backup</span>
					</label>

					{#if backupSettings.backup_enabled}
						<div class="flex items-center gap-4 text-sm">
							<label class="flex items-center gap-2">
								<span class="text-muted">Schedule:</span>
								<select
									value={backupSettings.backup_schedule ?? 'daily'}
									onchange={(e) => updateBackupSettings({ backup_schedule: e.currentTarget.value as 'daily' | 'weekly' })}
									class="rounded border border-border bg-background px-2 py-1 text-foreground"
								>
									<option value="daily">Daily</option>
									<option value="weekly">Weekly</option>
								</select>
							</label>

							<label class="flex items-center gap-2">
								<span class="text-muted">Keep:</span>
								<select
									value={backupSettings.backup_retention}
									onchange={(e) => updateBackupSettings({ backup_retention: +e.currentTarget.value })}
									class="rounded border border-border bg-background px-2 py-1 text-foreground"
								>
									<option value="3">3 versions</option>
									<option value="5">5 versions</option>
									<option value="10">10 versions</option>
								</select>
							</label>
						</div>
					{/if}

					{#if backupSettings.last_backup_at}
						<p class="text-xs text-muted">
							Last backup: {formatDate(backupSettings.last_backup_at)}
						</p>
					{/if}

					<button
						onclick={triggerBackup}
						disabled={actionLoading}
						class="rounded bg-accent/10 px-3 py-1.5 text-sm text-accent hover:bg-accent/20 disabled:opacity-50"
					>
						{actionLoading ? 'Working...' : 'Backup Now'}
					</button>
				</div>
			{/if}

			<!-- Backups List -->
			{#if backups.length > 0}
				<div class="rounded-lg border border-border bg-sidebar p-4 space-y-3">
					<h3 class="text-sm font-medium text-foreground">Backups ({backups.length})</h3>
					<div class="space-y-2 max-h-48 overflow-y-auto">
						{#each backups as backup (backup.id)}
							<div class="flex items-center justify-between rounded bg-background/50 p-2 text-xs">
								<div>
									<span class="font-medium">v{backup.version_number}</span>
									<span class="text-muted ml-2">{formatBytes(backup.backup_size_bytes)}</span>
									<span class="text-muted ml-2">
										{backup.entity_counts.notes}N {backup.entity_counts.todos}T
									</span>
									<p class="text-muted">{formatDate(backup.created_at)}</p>
								</div>
								<button
									onclick={() => restoreBackup(backup.id)}
									disabled={actionLoading}
									class="text-accent hover:underline disabled:opacity-50"
								>
									Restore
								</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
