// Drag-to-resize a column: the gesture, a width hook that remembers itself,
// and the look of the handle. Lifted from nuspace's sidebar so every app's
// resizable edge looks and behaves the same.
//
// A press that never travels past a few pixels is a click, not a drag: it
// moves nothing and fires `onClick` instead, which the width hook uses to snap
// back to its default.

import type * as React from "react";
import { useCallback, useState } from "react";
import { cn } from "./utils";

/** How far a press travels before it is a drag rather than a click. */
export const CLICK_SLOP = 3;

/**
 * Track one horizontal drag started by `e`. Listens on the window so a fast
 * pointer that leaves the handle keeps dragging, and holds a col-resize cursor
 * and no text selection on the body while it lasts. `onMove` gets the distance
 * from the start once the press has travelled past the slop, `onEnd` fires on
 * release of a drag, `onClick` instead when it never travelled. Primary button
 * only: returns false, and tracks nothing, for any other.
 */
export function trackColDrag(
	e: React.PointerEvent,
	onMove: (dx: number) => void,
	onEnd?: () => void,
	onClick?: () => void,
): boolean {
	if (e.button !== 0) return false;
	e.preventDefault();
	const startX = e.clientX;
	const body = document.body.style;
	const prevCursor = body.cursor;
	const prevSelect = body.userSelect;
	body.cursor = "col-resize";
	body.userSelect = "none";
	let dragging = false;
	const move = (ev: PointerEvent) => {
		const dx = ev.clientX - startX;
		if (!dragging && Math.abs(dx) < CLICK_SLOP) return;
		dragging = true;
		onMove(dx);
	};
	const up = (ev: PointerEvent) => {
		window.removeEventListener("pointermove", move);
		window.removeEventListener("pointerup", up);
		window.removeEventListener("pointercancel", up);
		body.cursor = prevCursor;
		body.userSelect = prevSelect;
		if (dragging) onEnd?.();
		else if (ev.type === "pointerup") onClick?.();
	};
	window.addEventListener("pointermove", move);
	window.addEventListener("pointerup", up);
	window.addEventListener("pointercancel", up);
	return true;
}

/** Sidebar width bounds, px, the same in every app. */
export const SIDEBAR_WIDTH = { MIN: 200, DEFAULT: 260, MAX: 540 } as const;

export type WidthBounds = { MIN: number; DEFAULT: number; MAX: number };

/**
 * A drag-resized width, kept in localStorage under `key` so a reload keeps it.
 * Storage can be missing or throw (private window, blocked site data), so
 * every read and write is guarded and the width falls back to the default.
 * `side` is which edge the handle rides: dragging a left edge leftwards widens.
 */
export function useResizableWidth(
	key: string,
	bounds: WidthBounds = SIDEBAR_WIDTH,
	side: "left" | "right" = "right",
): {
	width: number;
	onResizeStart: (e: React.PointerEvent) => void;
	onResizeReset: () => void;
} {
	const { MIN, DEFAULT, MAX } = bounds;
	const clamp = useCallback((w: number) => Math.min(MAX, Math.max(MIN, Math.round(w))), [MIN, MAX]);
	const [width, setWidth] = useState(() => {
		try {
			const raw = window.localStorage.getItem(key);
			const n = raw === null ? Number.NaN : Number(raw);
			return Number.isFinite(n) ? clamp(n) : DEFAULT;
		} catch {
			return DEFAULT;
		}
	});

	const save = useCallback(
		(w: number) => {
			try {
				window.localStorage.setItem(key, String(w));
			} catch {
				// Nothing to do: the width just will not survive a reload
			}
		},
		[key],
	);

	const onResizeReset = useCallback(() => {
		setWidth(DEFAULT);
		save(DEFAULT);
	}, [DEFAULT, save]);

	const onResizeStart = useCallback(
		(e: React.PointerEvent) => {
			const startW = width;
			let last = startW;
			trackColDrag(
				e,
				(dx) => {
					last = clamp(startW + (side === "right" ? dx : -dx));
					setWidth(last);
				},
				() => save(last),
				onResizeReset,
			);
		},
		[width, side, clamp, save, onResizeReset],
	);

	return { width, onResizeStart, onResizeReset };
}

/**
 * The handle's look: an 8px drag strip centred on the hairline, easy to hit
 * without eating content on either side. A 2px accent line fades in on hover
 * and while dragging. `side` is which edge of the positioned parent it rides.
 */
export function resizeHandleClasses(side: "left" | "right"): string {
	return cn(
		"group/resize absolute inset-y-0 z-30 w-2 cursor-col-resize touch-none",
		side === "left" ? "-left-1" : "-right-1",
		"after:absolute after:inset-y-0 after:left-1/2 after:w-0.5 after:-translate-x-1/2",
		"after:bg-accent after:opacity-0 after:transition-opacity after:duration-fast",
		"hover:after:opacity-60 active:after:opacity-100",
	);
}
