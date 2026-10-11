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

import type * as React from "react";
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

export function Grid({
	columns = 0,
	minWidth = 240,
	gap = 4,
	align = "stretch",
	padding = 0,
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
				className,
			)}
			style={{ gridTemplateColumns: gridTemplate(columns, minWidth, step), ...style }}
			{...props}
		/>
	);
}
