// Sizing -- height and scroll on a container, grow and basis for one child.
//
// The Python `sizing` props, read the same way by every container that takes
// them (Column, Row, Grid, Box):
//
//   height       the container is that tall. A number is px, text is a CSS
//                length ("60vh", "20rem", "100%").
//   max_height   it grows with what it holds, up to that.
//   scroll       "y" | "x" | "both" scroll what runs past the edge; "none"
//                (or unset) lets it show.
//
// A scrolling container gets min-h-0 / min-w-0 along its scroll axis, so in
// a flex parent it shrinks to the room it is given and scrolls inside it,
// instead of growing to its content and pushing the page.
//
// `grow` and `basis` are per child maps keyed by segment, kept by a Row or a
// Column (the child carries nothing): `readWeights` reads either off the wire.

import type { Path } from "@nustackdev/ui-core";
import type { CSSProperties } from "react";
import { useMemo } from "react";
import { useProp } from "../../tree";

export type Scroll = "none" | "y" | "x" | "both";

const SCROLL_CLASSES: Record<Scroll, string | undefined> = {
	none: undefined,
	y: "min-h-0 overflow-y-auto",
	x: "min-w-0 overflow-x-auto",
	both: "min-h-0 min-w-0 overflow-auto",
};

const LENGTH = /^\d+(\.\d+)?(px|rem|em|%|vh|vw|dvh|svh|lvh|ch)$/;

/** A length off the wire as CSS: a number is px, text passes when it reads as a length. */
export function cssLength(raw: unknown): string | undefined {
	if (typeof raw === "number") return Number.isFinite(raw) && raw >= 0 ? `${raw}px` : undefined;
	if (typeof raw !== "string") return undefined;
	const text = raw.trim();
	if (/^\d+$/.test(text)) return `${text}px`;
	return LENGTH.test(text) ? text : undefined;
}

export type Sizing = { className: string | undefined; style: CSSProperties | undefined };

/** The class and style a container's `height`, `max_height` and `scroll` props ask for. */
export function sizing(height: unknown, maxHeight: unknown, scroll: unknown): Sizing {
	const h = cssLength(height);
	const mh = cssLength(maxHeight);
	const className = SCROLL_CLASSES[(scroll as Scroll) ?? "none"] ?? undefined;
	const style = h || mh ? { height: h, maxHeight: mh } : undefined;
	return { className, style };
}

/** `sizing` for the container at `path`, kept stable while the props stay the same. */
export function useSizing(path: Path): Sizing {
	const height = useProp<unknown>(path, "height", null);
	const maxHeight = useProp<unknown>(path, "max_height", null);
	const scroll = useProp<unknown>(path, "scroll", "none");
	return useMemo(() => sizing(height, maxHeight, scroll), [height, maxHeight, scroll]);
}

export type Weights = Record<string, number>;

const NO_WEIGHTS: Weights = {};

/** A per child map off the wire (`grow`, `basis`): only whole numbers >= 0. */
export function readWeights(raw: unknown): Weights {
	if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return NO_WEIGHTS;
	const out: Weights = {};
	for (const [key, v] of Object.entries(raw as Record<string, unknown>)) {
		if (typeof v === "number" && Number.isFinite(v) && v >= 0) out[key] = v;
	}
	return Object.keys(out).length ? out : NO_WEIGHTS;
}

/** The container's `grow` and `basis` maps, kept stable while the props stay the same. */
export function useWeights(path: Path): { grow: Weights; basis: Weights } {
	const rawGrow = useProp<unknown>(path, "grow", null);
	const rawBasis = useProp<unknown>(path, "basis", null);
	return useMemo(
		() => ({ grow: readWeights(rawGrow), basis: readWeights(rawBasis) }),
		[rawGrow, rawBasis],
	);
}
