// Roving tabindex: a list of items that is one tab stop, the arrows moving
// focus inside it.
//
// A tree, a tab strip or a menu list with fifty items would otherwise be fifty
// tab stops. Exactly one item carries `tabIndex={0}` (the `tabKey`), every
// other one `-1`, and the keys below move focus between them.
//
// Items are found by a `data-key` attribute inside the container rather than
// through a ref per item, so an item can be any component (one that takes no
// ref included), and the lookup is the same whatever drew the items.

import type * as React from "react";
import { useCallback, useRef, useState } from "react";

export type RovingFocus = {
	/** Goes on the container the items are queried inside. */
	containerRef: React.RefObject<HTMLDivElement | null>;
	/** The one item in the tab order right now, null when there are none. */
	tabKey: string | null;
	/** What an item's `onFocus` calls, so the tab stop follows the caret. */
	setActiveKey: (key: string) => void;
	/** Move focus to an item by key. */
	focusKey: (key: string) => void;
	/** Move focus to an item by position, clamped to the ends. */
	focusIndex: (index: number) => void;
	/**
	 * The four moves every list shares: next, previous, first, last. Returns
	 * whether it took the event, so a caller can add its own keys on top.
	 */
	handleArrows: (e: React.KeyboardEvent, index: number) => boolean;
};

export type RovingOptions = {
	/** Which arrows step: up/down for a list or tree, left/right for a strip. */
	orientation?: "vertical" | "horizontal";
};

/** The attribute an item is found by. Spread `{[ROVING_KEY]: key}` on it. */
export const ROVING_KEY = "data-key";

/** A key quoted for an attribute selector. `CSS.escape` where there is one (not jsdom). */
function quote(key: string): string {
	return typeof CSS !== "undefined" && CSS.escape ? CSS.escape(key) : key.replace(/["\\]/g, "\\$&");
}

/**
 * `keys` is the items in render order; `selectedKey` is the one the app has
 * selected. The tab stop follows the caret, falls back to the selection, and
 * falls back again to the first item once whatever it was on is gone.
 */
export function useRovingFocus(
	keys: readonly string[],
	selectedKey: string | null = null,
	{ orientation = "vertical" }: RovingOptions = {},
): RovingFocus {
	const [activeKey, setActiveKey] = useState<string | null>(selectedKey);
	const containerRef = useRef<HTMLDivElement | null>(null);

	const tabKey =
		activeKey !== null && keys.includes(activeKey)
			? activeKey
			: selectedKey !== null && keys.includes(selectedKey)
				? selectedKey
				: (keys[0] ?? null);

	const focusKey = useCallback((key: string) => {
		setActiveKey(key);
		containerRef.current?.querySelector<HTMLElement>(`[${ROVING_KEY}="${quote(key)}"]`)?.focus();
	}, []);

	const focusIndex = useCallback(
		(index: number) => {
			const key = keys[Math.max(0, Math.min(keys.length - 1, index))];
			if (key !== undefined) focusKey(key);
		},
		[keys, focusKey],
	);

	const next = orientation === "vertical" ? "ArrowDown" : "ArrowRight";
	const prev = orientation === "vertical" ? "ArrowUp" : "ArrowLeft";

	const handleArrows = useCallback(
		(e: React.KeyboardEvent, index: number): boolean => {
			let to: number;
			if (e.key === next) to = index + 1;
			else if (e.key === prev) to = index - 1;
			else if (e.key === "Home") to = 0;
			else if (e.key === "End") to = keys.length - 1;
			else return false;
			e.preventDefault();
			focusIndex(to);
			return true;
		},
		[next, prev, keys.length, focusIndex],
	);

	return { containerRef, tabKey, setActiveKey, focusKey, focusIndex, handleArrows };
}
