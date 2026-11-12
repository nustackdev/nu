// Collapsible primitive. Wraps @radix-ui/react-collapsible.
// Design refs:
//   primitives.md    §Collapsible (thin wrapper, applies kit motion tokens)
//   motion.md        §3 Collapsible (content height base + ease-in-out)
//   a11y.md          §3 Collapsible (Radix wires Tab + Space/Enter)
//
// Simpler than Accordion: no roving focus, no group, single toggleable region.
// Content height animation rides Radix's --radix-collapsible-content-height.
//
// The content clips only while its height moves (and while closed): once
// open and still, a focus ring, a sticky header or a popover that is not
// portalled shows past its edge. `useClipWhileMoving` tracks the content's
// own height animation (a spinner's animation inside does not count); the
// Accordion content uses it too.

import { Collapsible as CollapsiblePrimitive } from "radix-ui";
import type * as React from "react";
import { useCallback, useState } from "react";

import { cn } from "../../lib/utils";

export function Collapsible({ ...props }: React.ComponentProps<typeof CollapsiblePrimitive.Root>) {
	return <CollapsiblePrimitive.Root data-slot="collapsible" {...props} />;
}

export function CollapsibleTrigger({
	className,
	...props
}: React.ComponentProps<typeof CollapsiblePrimitive.Trigger>) {
	return (
		<CollapsiblePrimitive.Trigger
			data-slot="collapsible-trigger"
			className={cn("cursor-default", className)}
			{...props}
		/>
	);
}

/**
 * Props that mark a disclosure's content `data-moving` while its own height
 * animation runs. Clip on `data-[moving]` and `data-[state=closed]`, not
 * always. Events from animations inside the content are ignored.
 */
export function useClipWhileMoving(
	onAnimationStart?: React.AnimationEventHandler<HTMLDivElement>,
	onAnimationEnd?: React.AnimationEventHandler<HTMLDivElement>,
) {
	const [moving, setMoving] = useState(false);
	const start = useCallback(
		(e: React.AnimationEvent<HTMLDivElement>) => {
			if (e.target === e.currentTarget) setMoving(true);
			onAnimationStart?.(e);
		},
		[onAnimationStart],
	);
	const end = useCallback(
		(e: React.AnimationEvent<HTMLDivElement>) => {
			if (e.target === e.currentTarget) setMoving(false);
			onAnimationEnd?.(e);
		},
		[onAnimationEnd],
	);
	return {
		"data-moving": moving ? "" : undefined,
		onAnimationStart: start,
		onAnimationEnd: end,
	};
}

/** Clip classes for a disclosure's content: only while moving or closed. */
export const CLIP_WHILE_MOVING =
	"data-[moving]:overflow-hidden data-[state=closed]:overflow-hidden";

export function CollapsibleContent({
	className,
	onAnimationStart,
	onAnimationEnd,
	...props
}: React.ComponentProps<typeof CollapsiblePrimitive.Content>) {
	const moving = useClipWhileMoving(onAnimationStart, onAnimationEnd);
	return (
		<CollapsiblePrimitive.Content
			data-slot="collapsible-content"
			className={cn(
				CLIP_WHILE_MOVING,
				"data-[state=open]:animate-collapsible-down",
				"data-[state=closed]:animate-collapsible-up",
				className,
			)}
			{...props}
			{...moving}
		/>
	);
}
