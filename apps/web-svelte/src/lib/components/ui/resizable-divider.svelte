<script lang="ts">
	/**
	 * Draggable divider for resizing panels.
	 * Tracks drag via mouse events and reports new size to parent.
	 */

	interface Props {
		orientation?: 'horizontal' | 'vertical';
		onresize?: (size: number) => void;
		class?: string;
	}

	let { orientation = 'vertical', onresize, class: className = '' }: Props = $props();

	let isDragging = $state(false);
	let dividerEl: HTMLDivElement | undefined = $state();
	let startPos = 0;
	let startSize = 0;

	function handleMouseDown(e: MouseEvent) {
		e.preventDefault();
		isDragging = true;

		if (orientation === 'vertical') {
			startPos = e.clientX;
			const prev = dividerEl?.previousElementSibling as HTMLElement | null;
			startSize = prev?.offsetWidth ?? 0;
		} else {
			startPos = e.clientY;
			const prev = dividerEl?.previousElementSibling as HTMLElement | null;
			startSize = prev?.offsetHeight ?? 0;
		}

		document.addEventListener('mousemove', handleMouseMove);
		document.addEventListener('mouseup', handleMouseUp);
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isDragging) return;
		const delta = orientation === 'vertical' ? e.clientX - startPos : e.clientY - startPos;
		onresize?.(startSize + delta);
	}

	function handleMouseUp() {
		isDragging = false;
		document.removeEventListener('mousemove', handleMouseMove);
		document.removeEventListener('mouseup', handleMouseUp);
	}

	const cursorClass = $derived(orientation === 'vertical' ? 'cursor-col-resize' : 'cursor-row-resize');
	const sizeClass = $derived(orientation === 'vertical' ? 'w-1' : 'h-1');
	const hoverClass = $derived(
		orientation === 'vertical' ? 'hover:w-1.5 active:w-1.5' : 'hover:h-1.5 active:h-1.5'
	);
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	bind:this={dividerEl}
	role="none"
	onmousedown={handleMouseDown}
	class="{sizeClass} {cursorClass} {hoverClass} shrink-0 bg-border hover:bg-accent/50 active:bg-accent transition-all {isDragging ? 'bg-accent' : ''} {className}"
></div>
