/**
 * Connection status store - tracks online/offline state and server connectivity.
 * Foundation for Phase 5 PWA/offline support.
 */

export type ConnectionStatus = 'online' | 'offline' | 'syncing';

class ConnectionStore {
	status = $state<ConnectionStatus>('online');
	lastSync = $state<Date | null>(null);
	pendingChanges = $state(0);

	constructor() {
		if (typeof window !== 'undefined') {
			// Initialize with current online status
			this.status = navigator.onLine ? 'online' : 'offline';

			// Listen for online/offline events
			window.addEventListener('online', () => this.handleOnline());
			window.addEventListener('offline', () => this.handleOffline());
		}
	}

	private handleOnline() {
		this.status = this.pendingChanges > 0 ? 'syncing' : 'online';
		// TODO Phase 5: Trigger sync of pending changes
	}

	private handleOffline() {
		this.status = 'offline';
	}

	/** Mark sync as started */
	startSync() {
		if (this.status !== 'offline') {
			this.status = 'syncing';
		}
	}

	/** Mark sync as completed */
	completeSync() {
		this.lastSync = new Date();
		this.pendingChanges = 0;
		if (navigator.onLine) {
			this.status = 'online';
		}
	}

	/** Add pending change (for offline queue) */
	addPendingChange() {
		this.pendingChanges++;
	}

	/** Clear pending changes */
	clearPending() {
		this.pendingChanges = 0;
	}
}

export const connectionStore = new ConnectionStore();
