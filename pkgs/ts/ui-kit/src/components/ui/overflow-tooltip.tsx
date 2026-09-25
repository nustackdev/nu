// OverflowTooltip: the full text of a truncated label, shown only while the
// ellipsis is actually hiding some of it.
//
// Whether the text is cut off is read when the tooltip asks to open, not on
// every render, so a resize or a rename needs nothing to keep it right. The
// measured box is the trigger or any element inside it, so a link whose inner
// span carries the ellipsis works the same as a bare span.
//
// A `right` tooltip that would run off the window opens below instead. Radix
// only ever flips to the opposite side, and left of a sidebar is off-screen
// too.

import type * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";

import {
	TOOLTIP_CHROME_PX,
	TOOLTIP_MAX_PX,
	TOOLTIP_SIDE_OFFSET,
	Tooltip,
	TooltipContent,
	TooltipTrigger,
} from "./tooltip";

type Side = "top" | "right" | "bottom" | "left";

/** The first box under `trigger`, itself included, that cuts its text off. */
function truncatedIn(trigger: HTMLElement | null): Element | null {
	if (!trigger) return null;
	if (trigger.scrollWidth > trigger.clientWidth) return trigger;
	for (const el of trigger.querySelectorAll("*")) {
		if (el.scrollWidth > el.clientWidth) return el;
	}
	return null;
}

/** Whether a tooltip for `text` fits to the right of `trigger`. */
function fitsRight(trigger: HTMLElement, text: Element): boolean {
	const width = Math.min(text.scrollWidth + TOOLTIP_CHROME_PX, TOOLTIP_MAX_PX);
	const right = trigger.getBoundingClientRect().right + TOOLTIP_SIDE_OFFSET + width;
	return right <= document.documentElement.clientWidth;
}

export interface OverflowTooltipProps {
	/** The full text. */
	label: string;
	side?: Side;
	/** Refuse to open, and close if open. Eg while the row is dragged. */
	disabled?: boolean;
	/** The trigger, rendered `asChild`, so it keeps its own element and handlers. */
	children: React.ReactElement;
}

export function OverflowTooltip({
	label,
	side = "top",
	disabled = false,
	children,
}: OverflowTooltipProps) {
	const trigger = useRef<HTMLElement | null>(null);
	// A callback, since TooltipTrigger types its ref as a button and `asChild`
	// puts whatever element the caller hands in there.
	const triggerRef = useCallback((el: HTMLElement | null) => {
		trigger.current = el;
	}, []);
	const [open, setOpen] = useState(false);
	const [at, setAt] = useState<Side>(side);

	// A drag that starts under an open tooltip closes it for good, so it does
	// not come back once the drag ends.
	useEffect(() => {
		if (disabled) setOpen(false);
	}, [disabled]);

	const onOpenChange = useCallback(
		(next: boolean) => {
			if (!next || disabled) {
				setOpen(false);
				return;
			}
			const el = trigger.current;
			const text = truncatedIn(el);
			if (!el || !text) return;
			setAt(side === "right" && !fitsRight(el, text) ? "bottom" : side);
			setOpen(true);
		},
		[disabled, side],
	);

	return (
		<Tooltip open={open && !disabled} onOpenChange={onOpenChange}>
			<TooltipTrigger asChild ref={triggerRef}>
				{children}
			</TooltipTrigger>
			<TooltipContent side={at}>{label}</TooltipContent>
		</Tooltip>
	);
}
