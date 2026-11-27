// Anchor tip: one small floating tip, fixed above an element, for the data
// views that keep one shared tip instead of a tooltip per mark (calendar
// heatmap days, timeline bars, waterfall spans).
//
// Design refs:
//   space-radius.md  §Density Tooltip (pad 4x8, radius `sm`, text-xs)
//   palette.md       backgrounds (bg-bg-elevated), the tooltip's own look
//
// It is the kit tooltip's look without Radix: no trigger, no hover state, so
// it also shows in touch mode, where a tooltip never opens. That is its use
// there: a tap on a mark shows what the desktop hover says, in place, over
// the mark (language/mobile.md). `useTapAway` is the other half: the next
// tap outside the marks, or any scroll (the tip is fixed to where the mark
// was), hides it.
//
// The tip is placed once per anchor, centred above it, as wide as what it
// says (up to the tooltip's max), not the room left of it near an edge.
// `keepOnScreen` (touch mode, a phone) shifts it back inside the screen, 8px
// clear of either edge.

import type * as React from "react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { usePortalContainer } from "../../lib/portal";
import { cn } from "../../lib/utils";

export interface AnchorTipProps {
	/** The mark the tip sits over. Null hides it. */
	anchor: Element | null | undefined;
	/** The tip's data-slot, named for its view ("timeline-tip"). */
	slot: string;
	/** Shift the tip back inside the screen, for a phone (touch mode). */
	keepOnScreen?: boolean;
	className?: string;
	children?: React.ReactNode;
}

/** The one floating tip, fixed above `anchor`. */
export function AnchorTip({ anchor, slot, keepOnScreen, className, children }: AnchorTipProps) {
	const portal = usePortalContainer();
	const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
	const [shift, setShift] = useState(0);
	const tipRef = useRef<HTMLDivElement>(null);
	useLayoutEffect(() => {
		if (!anchor) {
			setPos(null);
			return;
		}
		const r = anchor.getBoundingClientRect();
		setPos({ x: r.left + r.width / 2, y: r.top });
		setShift(0);
	}, [anchor]);
	// Measured once placed: how far it pokes past either edge, 8px clear.
	useLayoutEffect(() => {
		const el = tipRef.current;
		if (!keepOnScreen || !el || !pos) return;
		const w = el.offsetWidth;
		const room = document.documentElement.clientWidth;
		const left = pos.x - w / 2;
		const next = left < 8 ? 8 - left : left + w > room - 8 ? room - 8 - (left + w) : 0;
		setShift((prev) => (prev === next ? prev : next));
	}, [keepOnScreen, pos]);
	if (!anchor || !pos || typeof document === "undefined") return null;
	return createPortal(
		<div
			data-slot={slot}
			role="tooltip"
			className={cn(
				"pointer-events-none fixed z-50 -translate-x-1/2 -translate-y-full w-max max-w-xs px-2 py-1 rounded-sm",
				"bg-bg-elevated text-text-primary border border-border-default shadow-floating",
				"text-xs leading-tight",
				className,
			)}
			ref={tipRef}
			style={{ left: pos.x + shift, top: pos.y - 6 }}
		>
			{children}
		</div>,
		portal ?? document.body,
	);
}

/**
 * While `on`, call `away` on a pointer down that `keep` does not claim (a
 * tap outside the marks), or on any scroll. A tap that `keep` claims is the
 * view's own: it moves the tip, or hides it, itself.
 */
export function useTapAway(on: boolean, keep: (target: Node) => boolean, away: () => void) {
	// The latest callbacks, so the listeners stay put while the view renders.
	const latest = useRef({ keep, away });
	latest.current = { keep, away };
	useEffect(() => {
		if (!on) return;
		const hide = (e: Event) => {
			if (e.type === "pointerdown" && latest.current.keep(e.target as Node)) return;
			latest.current.away();
		};
		document.addEventListener("pointerdown", hide, true);
		window.addEventListener("scroll", hide, true);
		return () => {
			document.removeEventListener("pointerdown", hide, true);
			window.removeEventListener("scroll", hide, true);
		};
	}, [on]);
}
