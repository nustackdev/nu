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
import { useCallback, useLayoutEffect, useRef, useState } from "react";

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
 *
 * `animationstart` lands a frame after the animation began, so on its own
 * the first frame of an open would draw the whole content over a box that
 * is barely open. The mark is also set before paint: when the content
 * mounts (Radix mounts it on open) and whenever its `data-state` flips, if
 * an animation of its own is running then. One that never runs (reduced
 * motion, the first open of a box born open) never marks it.
 */
export function useClipWhileMoving(
	onAnimationStart?: React.AnimationEventHandler<HTMLDivElement>,
	onAnimationEnd?: React.AnimationEventHandler<HTMLDivElement>,
	forwardedRef?: React.Ref<HTMLDivElement>,
) {
	const [moving, setMoving] = useState(false);
	const node = useRef<HTMLDivElement | null>(null);
	const forwarded = useRef(forwardedRef);
	forwarded.current = forwardedRef;
	const ref = useCallback((el: HTMLDivElement | null) => {
		node.current = el;
		const r = forwarded.current;
		if (typeof r === "function") r(el);
		else if (r) (r as React.RefObject<HTMLDivElement | null>).current = el;
	}, []);
	useLayoutEffect(() => {
		const el = node.current;
		if (!el || typeof el.getAnimations !== "function") return;
		const check = () => {
			if (el.getAnimations().length === 0) return;
			// Straight on the node too: a flip lands in a microtask, and the
			// render the state asks for may come after the next paint.
			el.setAttribute("data-moving", "");
			setMoving(true);
		};
		check();
		const watch = new MutationObserver(check);
		watch.observe(el, { attributes: true, attributeFilter: ["data-state"] });
		return () => watch.disconnect();
	}, []);
	const start = useCallback(
		(e: React.AnimationEvent<HTMLDivElement>) => {
			if (e.target === e.currentTarget) setMoving(true);
			onAnimationStart?.(e);
		},
		[onAnimationStart],
	);
	const end = useCallback(
		(e: React.AnimationEvent<HTMLDivElement>) => {
			if (e.target === e.currentTarget) {
				e.currentTarget.removeAttribute("data-moving");
				setMoving(false);
			}
			onAnimationEnd?.(e);
		},
		[onAnimationEnd],
	);
	return {
		ref,
		"data-moving": moving ? "" : undefined,
		onAnimationStart: start,
		onAnimationEnd: end,
	};
}

/**
 * Clip classes for a disclosure's content: only while moving or closed. The
 * content is always its own formatting context (`flow-root`), so a child's
 * margin stays inside it: Radix measures the same height the content takes
 * while it clips, and nothing jumps when the clip lifts at the end.
 */
export const CLIP_WHILE_MOVING =
	"flow-root data-[moving]:overflow-hidden data-[state=closed]:overflow-hidden";

export function CollapsibleContent({
	className,
	onAnimationStart,
	onAnimationEnd,
	ref,
	...props
}: React.ComponentProps<typeof CollapsiblePrimitive.Content>) {
	const moving = useClipWhileMoving(onAnimationStart, onAnimationEnd, ref);
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
