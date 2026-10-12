// Drag-to-resize: the gesture, a width hook that remembers itself, and the
// look of the handle. Lifted from nuspace's sidebar so every app's resizable
// edge looks and behaves the same. The split panels (`Resizable`) ride the
// same gesture and the same accent line, on either axis.
//
// A press that never travels past a few pixels is a click, not a drag: it
// moves nothing and fires `onClick` instead, which the width hook uses to snap
// back to its default.

import type * as React from "react";
import { useCallback, useState } from "react";
import { cn } from "./utils";

/** How far a press travels before it is a drag rather than a click. */
export const CLICK_SLOP = 3;

/** Which way a drag moves: `x` resizes columns, `y` resizes rows. */
export type DragAxis = "x" | "y";

/**
 * Track one drag along `axis` started by `e`. Listens on the window so a fast
 * pointer that leaves the handle keeps dragging, and holds the matching resize
 * cursor (col-resize or row-resize) and no text selection on the body while
 * it lasts. `onMove` gets the distance from the start once the press has
 * travelled past the slop, `onEnd` fires on release of a drag, `onClick`
 * instead when it never travelled. Primary button only: returns false, and
 * tracks nothing, for any other.
 */
export function trackDrag(
	e: React.PointerEvent,
	axis: DragAxis,
	onMove: (delta: number) => void,
	onEnd?: () => void,
	onClick?: () => void,
): boolean {
	if (e.button !== 0) return false;
	e.preventDefault();
	const start = axis === "x" ? e.clientX : e.clientY;
	const body = document.body.style;
	const prevCursor = body.cursor;
	const prevSelect = body.userSelect;
	body.cursor = axis === "x" ? "col-resize" : "row-resize";
	body.userSelect = "none";
	let dragging = false;
	const move = (ev: PointerEvent) => {
		const d = (axis === "x" ? ev.clientX : ev.clientY) - start;
		if (!dragging && Math.abs(d) < CLICK_SLOP) return;
		dragging = true;
		onMove(d);
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

/** `trackDrag` on the x axis: one horizontal drag, for a column's edge. */
export function trackColDrag(
	e: React.PointerEvent,
	onMove: (dx: number) => void,
	onEnd?: () => void,
	onClick?: () => void,
): boolean {
	return trackDrag(e, "x", onMove, onEnd, onClick);
}

/**
 * Read `key` from localStorage. Storage can be missing or throw (private
 * window, blocked site data), so this answers null instead.
 */
export function readStored(key: string): string | null {
	try {
		return window.localStorage.getItem(key);
	} catch {
		return null;
	}
}

/** Write `key` to localStorage, quietly doing nothing when storage throws. */
export function writeStored(key: string, value: string): void {
	try {
		window.localStorage.setItem(key, value);
	} catch {
		// Nothing to do: the value just will not survive a reload
	}
}

/** Sidebar width bounds, px, the same in every app. */
export const SIDEBAR_WIDTH = { MIN: 200, DEFAULT: 260, MAX: 540 } as const;

export type WidthBounds = { MIN: number; DEFAULT: number; MAX: number };

/**
 * A drag-resized width, kept in localStorage under `key` so a reload keeps it.
 * A width that is missing or unreadable falls back to the default.
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
		const raw = readStored(key);
		const n = raw === null ? Number.NaN : Number(raw);
		return Number.isFinite(n) ? clamp(n) : DEFAULT;
	});

	const save = useCallback((w: number) => writeStored(key, String(w)), [key]);

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
 * The accent line every resize handle draws in its `after` box: hidden at
 * rest, fading in on hover, full while pressed or while a drag is live
 * (`data-dragging`, which outlasts `:active` when the pointer leaves).
 */
const resizeLine = [
	"after:absolute after:bg-accent after:opacity-0 after:transition-opacity after:duration-fast",
	"hover:after:opacity-60 active:after:opacity-100 data-[dragging]:after:opacity-100",
].join(" ");

/**
 * The handle's look: an 8px drag strip centred on the hairline, easy to hit
 * without eating content on either side. A 2px accent line fades in on hover
 * and while dragging. `side` is which edge of the positioned parent it rides.
 */
export function resizeHandleClasses(side: "left" | "right"): string {
	return cn(
		"group/resize absolute inset-y-0 z-30 w-2 cursor-col-resize touch-none",
		side === "left" ? "-left-1" : "-right-1",
		"after:inset-y-0 after:left-1/2 after:w-0.5 after:-translate-x-1/2",
		resizeLine,
	);
}

/**
 * The look of a handle between two split panels. Unlike the edge handle it
 * sits in the flow, as the 1px hairline that divides them, and its `before`
 * box widens the hit area to 8px over both neighbours. `orientation` is the
 * group's: a horizontal group puts its panels side by side, so the handle is
 * a vertical line with a col-resize cursor, and the other way round.
 */
export function splitHandleClasses(orientation: "horizontal" | "vertical"): string {
	return cn(
		"group/resize relative z-10 shrink-0 touch-none bg-border-subtle focus-ring",
		"before:absolute",
		orientation === "horizontal"
			? [
					"w-px self-stretch cursor-col-resize",
					"before:inset-y-0 before:left-1/2 before:w-2 before:-translate-x-1/2",
					"after:inset-y-0 after:left-1/2 after:w-0.5 after:-translate-x-1/2",
				]
			: [
					"h-px self-stretch cursor-row-resize",
					"before:inset-x-0 before:top-1/2 before:h-2 before:-translate-y-1/2",
					"after:inset-x-0 after:top-1/2 after:h-0.5 after:-translate-y-1/2",
				],
		resizeLine,
	);
}
