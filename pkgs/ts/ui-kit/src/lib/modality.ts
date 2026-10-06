// Which hand moved last: the keyboard or a pointer.
//
// Some chrome belongs to where you are working, and "where" depends on how.
// A table's row and column handles are the case in point. Working with the
// pointer, they belong under the pointer, and gone when it leaves; working
// from the keyboard, they belong on the focused cell or the caret, wherever
// the pointer happens to rest. Focus alone cannot tell the two apart: a click
// focuses a cell too, and handles that then stayed on the last cell clicked
// would look stuck there. So the host asks this instead.
//
// A key pressed in the element counts as the keyboard, a lone modifier
// excepted (shift held for a shift-click is still the pointer's). A pointer
// pressed in it counts as the pointer, and so does one moved over it: having
// typed into a cell, you reach for the mouse, and the handles should follow
// it from there, not jump back to the cell you typed in once it moves on. A
// move that goes nowhere (the browser sends those when the page scrolls under
// a resting pointer) is not the hand moving. All of it is watched in the
// capture phase, so the answer is in before any handler of the element's own
// reads it.

const MODIFIERS = new Set(["Shift", "Control", "Alt", "Meta", "CapsLock", "Fn"]);

/**
 * Report the last input over `el` to `onChange`, true for the keyboard and
 * false for a pointer, only when it changes. Returns the unsubscribe.
 */
export function watchKeyboardUse(
	el: HTMLElement,
	onChange: (keyboard: boolean) => void,
): () => void {
	let keyboard: boolean | null = null;
	const set = (next: boolean) => {
		if (next === keyboard) return;
		keyboard = next;
		onChange(next);
	};
	const key = (e: KeyboardEvent) => {
		if (!MODIFIERS.has(e.key)) set(true);
	};
	const pointer = () => set(false);
	let x: number | null = null;
	let y: number | null = null;
	const move = (e: PointerEvent) => {
		if (x !== null && (e.screenX !== x || e.screenY !== y)) set(false);
		x = e.screenX;
		y = e.screenY;
	};
	el.addEventListener("keydown", key, true);
	el.addEventListener("pointerdown", pointer, true);
	el.addEventListener("pointermove", move, true);
	return () => {
		el.removeEventListener("keydown", key, true);
		el.removeEventListener("pointerdown", pointer, true);
		el.removeEventListener("pointermove", move, true);
	};
}
