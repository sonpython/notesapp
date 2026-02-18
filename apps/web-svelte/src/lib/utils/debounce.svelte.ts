/**
 * Debounce utility for Svelte 5 runes.
 */

export function createDebounced<T>(initialValue: T, delay: number) {
	let value = $state(initialValue);
	let debounced = $state(initialValue);
	let timer: ReturnType<typeof setTimeout>;

	function set(newValue: T) {
		value = newValue;
		clearTimeout(timer);
		timer = setTimeout(() => {
			debounced = newValue;
		}, delay);
	}

	function setImmediate(newValue: T) {
		value = newValue;
		debounced = newValue;
		clearTimeout(timer);
	}

	return {
		get value() {
			return value;
		},
		get debounced() {
			return debounced;
		},
		set,
		setImmediate
	};
}

/**
 * Simple debounce function for callbacks.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(fn: T, delay: number): T {
	let timer: ReturnType<typeof setTimeout>;
	return ((...args: unknown[]) => {
		clearTimeout(timer);
		timer = setTimeout(() => fn(...args), delay);
	}) as T;
}
