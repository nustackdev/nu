// ScrollArea primitive: a scroller with overlay scrollbars.
// Design refs:
//   palette.md       borders (thumb on border-strong, text-muted on hover)
//   motion.md        §1 (`duration-base` fade in, `ease-out` / `ease-in`)
//   a11y.md          §1 (inset ring when the viewport takes focus)
//
// Radix ScrollArea underneath: the viewport is a native scroller with its own
// scrollbar hidden, so wheel, trackpad and keyboard scrolling stay the
// browser's. The kit draws thin bars on top of the content, out of the layout,
// in the macOS way: shown while scrolling or while the pointer is on the
// track, faded out after.
//
// The bars are always mounted and hidden with opacity, not unmounted. Radix
// alone ignores a pointer on a hidden track, so a hidden bar would never come
// back on hover; mounted, a CSS hover brings it back and a drag on its thumb
// scrolls. A bar with nothing to scroll has no thumb, and then lets the
// pointer through to the content under it.
//
// `viewportRef` reaches the scrolling element, for a caller that reads or sets
// `scrollLeft` / `scrollTop` or scrolls a child into view.

import { ScrollArea as ScrollAreaPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

export type ScrollAreaOrientation = "vertical" | "horizontal" | "both";

export interface ScrollAreaProps extends React.ComponentProps<typeof ScrollAreaPrimitive.Root> {
	/** Which axes scroll. The others are clipped. */
	orientation?: ScrollAreaOrientation;
	/** The viewport, the element that actually scrolls. */
	viewportRef?: React.Ref<HTMLDivElement>;
	viewportClassName?: string;
}

function ScrollArea({
	className,
	children,
	orientation = "vertical",
	type = "scroll",
	scrollHideDelay = 600,
	viewportRef,
	viewportClassName,
	...props
}: ScrollAreaProps) {
	const vertical = orientation !== "horizontal";
	const horizontal = orientation !== "vertical";
	return (
		<ScrollAreaPrimitive.Root
			data-slot="scroll-area"
			data-orientation={orientation}
			type={type}
			scrollHideDelay={scrollHideDelay}
			className={cn("relative overflow-hidden", className)}
			{...props}
		>
			<ScrollAreaPrimitive.Viewport
				ref={viewportRef}
				data-slot="scroll-area-viewport"
				className={cn(
					"size-full rounded-[inherit]",
					"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
					// Radix wraps the content in a `display: table` box that grows
					// to its widest child. With no sideways scroll that box would
					// push rows past the edge and clip them instead of letting
					// them truncate, so a vertical only area keeps it a block.
					!horizontal && "[&>div]:block!",
					// A horizontal only area keeps the box growing sideways, but as
					// a block as tall as the viewport: Firefox resolves no percent
					// height inside a table, so `h-full` content collapsed to 0.
					orientation === "horizontal" && "[&>div]:block! [&>div]:h-full [&>div]:w-max",
					viewportClassName,
				)}
			>
				{children}
			</ScrollAreaPrimitive.Viewport>
			{vertical && <ScrollBar orientation="vertical" />}
			{horizontal && <ScrollBar orientation="horizontal" />}
		</ScrollAreaPrimitive.Root>
	);
}

function ScrollBar({
	className,
	orientation = "vertical",
	...props
}: React.ComponentProps<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>) {
	return (
		<ScrollAreaPrimitive.ScrollAreaScrollbar
			data-slot="scroll-area-scrollbar"
			orientation={orientation}
			forceMount
			className={cn(
				"group/scrollbar z-10 flex touch-none select-none p-0.5",
				orientation === "vertical" ? "h-full w-2" : "h-2 flex-col",
				"transition-opacity",
				"data-[state=visible]:opacity-100 data-[state=visible]:duration-base data-[state=visible]:ease-out",
				"data-[state=hidden]:opacity-0 data-[state=hidden]:duration-base data-[state=hidden]:ease-in",
				"hover:opacity-100! hover:duration-fast! hover:ease-out!",
				"not-has-[[data-slot=scroll-area-thumb]]:pointer-events-none",
				className,
			)}
			{...props}
		>
			<ScrollAreaPrimitive.ScrollAreaThumb
				data-slot="scroll-area-thumb"
				className={cn(
					"relative flex-1 rounded-full bg-border-strong",
					"transition-colors duration-fast ease-out",
					"group-hover/scrollbar:bg-text-muted",
				)}
			/>
		</ScrollAreaPrimitive.ScrollAreaScrollbar>
	);
}

export { ScrollArea };
