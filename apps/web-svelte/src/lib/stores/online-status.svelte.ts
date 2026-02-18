/**
 * Online status store - tracks browser online/offline state.
 */

import { browser } from '$app/environment';

class OnlineStatusStore {
	isOnline = $state(true);

	constructor() {
		if (browser) {
			this.isOnline = navigator.onLine;
			window.addEventListener('online', () => {
				this.isOnline = true;
			});
			window.addEventListener('offline', () => {
				this.isOnline = false;
			});
		}
	}
}

export const onlineStatus = new OnlineStatusStore();
