// Grid primitive. Equal cells, row after row, as many per row as the width
// allows.
// Design refs:
//   language/space-radius.md  §grid (4px), §spacing (gap and padding steps)
//   space-radius.md           §1 spacing scale (Tailwind step names)
//
// `columns` caps the cells on a row (0: no cap), `minWidth` is the narrowest
// a cell gets. Every track is the same width, so a dashboard of stat cards
// or a gallery lines up without per-cell sizing:
//
//   columns 0   as many columns as fit at minWidth
//   columns N   at most N, never narrower than minWidth (a phone stacks)
//
// The track list is an inline style, not a class: it is computed from the
// props, and Tailwind v4 only ships class names it saw written out. Gap and
// padding are steps on the spacing ladder, mapped statically for the same
// reason. Tracks auto-fill, so three cells in a four-column grid keep the
// width of a quarter instead of stretching to a third.
//
// Cells get min-width 0, so a chart or a long line in one never pushes its
// track wider than the others. No outer margin: a grid placed in a layout is
// spaced by that layout.
//
// A cell may span: `gridSpan` is the placement for one cell `cols` tracks
// wide and `rows` tall, clamped to the tracks the grid has right now, so a
// two-wide feature cell in a grid that has stacked to one column is one wide
// and one tall, never an overflowing implicit track. `useTrackCount` keeps
// that number for the grid's current width. `dense` lets later cells fill the holes
// a wide one leaves, which a bento layout wants.

import type * as React from "react";
import { useLayoutEffect, useState } from "react";
import { cn } from "../../lib/utils";

export type GridAlign = "stretch" | "start" | "center" | "end";

const GAP_CLASSES: Record<number, string> = {
	0: "gap-0",
	1: "gap-1",
	2: "gap-2",
	3: "gap-3",
	4: "gap-4",
	5: "gap-5",
	6: "gap-6",
	8: "gap-8",
	10: "gap-10",
	12: "gap-12",
};

const PADDING_CLASSES: Record<number, string> = {
	0: "p-0",
	1: "p-1",
	2: "p-2",
	3: "p-3",
	4: "p-4",
	5: "p-5",
	6: "p-6",
	8: "p-8",
	10: "p-10",
	12: "p-12",
};

const ALIGN_CLASSES: Record<GridAlign, string> = {
	stretch: "items-stretch",
	start: "items-start",
	center: "items-center",
	end: "items-end",
};

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
	/** At most this many cells on a row. 0 (default) lets the width decide. */
	columns?: number;
	/** The narrowest a cell gets, in px. Default 240. */
	minWidth?: number;
	/** Space between cells, a spacing step (0, 1, 2, 3, 4, 5, 6, 8, 10, 12). Default 4. */
	gap?: number;
	/** Where each cell sits along its row. "stretch" (default) evens out the heights. */
	align?: GridAlign;
	/** Inner padding, a spacing step like `gap`. Default 0. */
	padding?: number;
	/** Backfill: a later cell takes an earlier hole a spanning cell left. Default false. */
	dense?: boolean;
	ref?: React.Ref<HTMLDivElement>;
}

/** The track list for `columns` and `minWidth`, with `gap` as a spacing step. */
export function gridTemplate(columns: number, minWidth: number, gap: number): string {
	const min = `${Math.max(0, minWidth)}px`;
	const n = Math.floor(columns);
	if (n < 1) return `repeat(auto-fill, minmax(min(100%, ${min}), 1fr))`;
	// One track per column: a share of the width after the gaps between N
	// cells, never under `min`, never over the whole row.
	const share = `(100% - ${n - 1} * var(--spacing) * ${gap}) / ${n}`;
	return `repeat(auto-fill, minmax(min(100%, max(${min}, ${share})), 1fr))`;
}

/**
 * Placement for a cell `cols` tracks wide and `rows` tall in a grid of
 * `tracks` columns. Wider than the grid clamps to the grid; a grid stacked
 * to one column drops the row span too, so the cell is one plain cell.
 */
export function gridSpan(cols: number, rows: number, tracks: number): React.CSSProperties {
	const fit = Math.max(1, Math.floor(tracks));
	const c = Math.min(Math.max(1, Math.floor(cols) || 1), fit);
	const r = fit === 1 ? 1 : Math.max(1, Math.floor(rows) || 1);
	return {
		gridColumn: c > 1 ? `span ${c} / span ${c}` : undefined,
		gridRow: r > 1 ? `span ${r} / span ${r}` : undefined,
	};
}

/**
 * How many tracks `gridTemplate(columns, minWidth, ...)` lays out in a grid
 * `width` px wide (inside its padding) with `gapPx` between cells: the same
 * auto-fill arithmetic the browser does, at least 1.
 */
export function trackCount(
	width: number,
	columns: number,
	minWidth: number,
	gapPx: number,
): number {
	const n = Math.floor(columns);
	const w = Math.max(0, width);
	const share = n >= 1 ? (w - (n - 1) * gapPx) / n : 0;
	const track = Math.min(w, Math.max(Math.max(0, minWidth), share));
	// Half a pixel of slack: a share computed from the width fits exactly.
	const fit = track > 0 ? Math.floor((w + gapPx + 0.5) / (track + gapPx)) : 1;
	return Math.max(1, n >= 1 ? Math.min(fit, n) : fit);
}

/**
 * How many column tracks the grid in `el` lays out now, kept current as it
 * resizes. Computed from its width rather than read off its track list,
 * since a cell spanning more tracks than there are adds implicit ones to
 * that list. `fallback` until the first measure, or where nothing measures
 * (no ResizeObserver, as under jsdom). Off when `enabled` is false, so a grid
 * with no spanning cell observes nothing.
 */
export function useTrackCount(
	el: HTMLElement | null,
	columns: number,
	minWidth: number,
	fallback: number,
	enabled = true,
): number {
	const [tracks, setTracks] = useState(fallback);
	useLayoutEffect(() => {
		if (!el || !enabled || typeof ResizeObserver === "undefined") return;
		const measure = () => {
			const style = getComputedStyle(el);
			const width =
				el.clientWidth -
				Number.parseFloat(style.paddingLeft) -
				Number.parseFloat(style.paddingRight);
			const gap = Number.parseFloat(style.columnGap) || 0;
			setTracks(trackCount(width, columns, minWidth, gap));
		};
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(el);
		return () => observer.disconnect();
	}, [el, columns, minWidth, enabled]);
	return tracks;
}

export function Grid({
	columns = 0,
	minWidth = 240,
	gap = 4,
	align = "stretch",
	padding = 0,
	dense = false,
	className,
	style,
	...props
}: GridProps) {
	const step = gap in GAP_CLASSES ? gap : 4;
	return (
		<div
			data-slot="grid"
			className={cn(
				"grid *:min-w-0",
				GAP_CLASSES[step],
				PADDING_CLASSES[padding] ?? PADDING_CLASSES[0],
				ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch,
				dense && "grid-flow-row-dense",
				className,
			)}
			style={{ gridTemplateColumns: gridTemplate(columns, minWidth, step), ...style }}
			{...props}
		/>
	);
}
