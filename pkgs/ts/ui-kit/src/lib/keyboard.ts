// Keys that belong to one element, not to the page.
//
// A surface that navigates with the arrow keys has to answer the question
// "whose arrows are these" before it binds anything. A document or window
// listener cannot: two of these on one page both fire, and one sitting next to
// a text field eats the caret keys. So the binding goes on the element, it
// carries a tab stop so the element can hold focus at all, and the browser's
// own focus routing decides who hears the key. Nested scopes work for free,
// because a handled key stops propagating and the innermost one wins.

import { type KeyboardEvent, useCallback, useRef } from "react";

/** Key name (the DOM `event.key`) to what it does. */
export type KeyBindings = Record<string, (event: KeyboardEvent<HTMLElement>) => void>;

export type KeyScope<E extends HTMLElement> = {
	tabIndex: number;
	onKeyDown: (event: KeyboardEvent<E>) => void;
};

/**
 * Props to spread on the element that owns these keys.
 *
 * A key with a binding is handled and consumed; anything else passes through
 * untouched, so a browser shortcut or a parent scope still sees it. Chords are
 * deliberately out: a modifier means the key belongs to the browser or to the
 * OS, and a list that quietly swallowed cmd+ArrowLeft would be a surface you
 * cannot navigate back out of.
 *
 * The bindings are read fresh on every event, so a handler closing over this
 * render's state does not have to be stable.
 */
export function useKeyScope<E extends HTMLElement = HTMLElement>(
	bindings: KeyBindings,
): KeyScope<E> {
	const live = useRef(bindings);
	live.current = bindings;
	const onKeyDown = useCallback((event: KeyboardEvent<E>) => {
		if (event.altKey || event.ctrlKey || event.metaKey) return;
		const handler = live.current[event.key];
		if (!handler) return;
		event.preventDefault();
		event.stopPropagation();
		handler(event);
	}, []);
	return { tabIndex: 0, onKeyDown };
}
