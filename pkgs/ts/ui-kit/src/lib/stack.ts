// The stack width: the one width a placed layout gives up its columns at.
//
// Layout follows a component's own width, never the screen's (see
// language/mobile.md "layout"). Fluid layouts (equal grids, wrapping rows)
// reflow on their own and need no number. Placed ones (a "2fr 1fr" board, a
// split of fill children side by side) cannot squeeze forever, so below this
// width they stack into one column, in source order. A resizable group is not
// one of them: its handles let a pointer make room, so only touch stacks it.
// One width for the whole kit, so a board and a split in the same narrow
// column give up at the same moment.
//
// The CSS side is the theme's `--container-stack` token (theme.css), the same
// 560px, which gives container query variants by name: `@stack:` from it up,
// `@max-stack:` below it, on any element under an `@container`. Change one,
// change both.
//
// `useStacked` is the JS side, for a component that measures its own box
// (a grid cannot query itself): true while the element is narrower than the
// width. Off, unmeasured, or where nothing measures (no ResizeObserver, as
// under jsdom), it is false, so the wide layout is what renders first.

import { useLayoutEffect, useState } from "react";

/** Placed layouts stack below this width, in px. The CSS twin is `--container-stack`. */
export const STACK_WIDTH = 560;

/**
 * Whether `el` is narrower than `below` px, kept current as it resizes.
 * False while `enabled` is false, before the first measure, and for a
 * `below` of 0 or less (never stacks).
 */
export function useStacked(el: HTMLElement | null, below = STACK_WIDTH, enabled = true): boolean {
	const on = enabled && below > 0;
	const [stacked, setStacked] = useState(false);
	useLayoutEffect(() => {
		if (!el || !on || typeof ResizeObserver === "undefined") return;
		// A box not laid out yet (inside a hidden tab) reads 0: no answer.
		const measure = () => {
			const width = el.clientWidth;
			if (width > 0) setStacked(width < below);
		};
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(el);
		return () => observer.disconnect();
	}, [el, on, below]);
	return on && stacked;
}
