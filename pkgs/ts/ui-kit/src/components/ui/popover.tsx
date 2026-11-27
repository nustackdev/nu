// Popover primitive: anchored floating content, not focus-trapping.
// Design refs:
//   primitives.md    §Popover (parts, motion)
//   palette.md       backgrounds, borders
//   space-radius.md  §Density Popover (pad 12, radius `md`)
//   motion.md        §3 Popover (`duration-base` fade+y-shift)
//   a11y.md          §3 Popover (Esc, focus restore, no trap)
//
// In touch mode (../../lib/touch.ts) the same parts render a bottom sheet
// (./bottom-sheet.tsx): the root, trigger and close map one to one, the
// content drops its placement props and fills the sheet, the arrow is gone
// and the anchor is a plain box. Callers change nothing. This is the pattern
// for every overlay in the kit: read `useTouch()` once at the top, branch.

import { Popover as PopoverPrimitive, Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";

import { usePortalContainer } from "../../lib/portal";
import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import {
	BottomSheet,
	BottomSheetClose,
	BottomSheetContent,
	BottomSheetTrigger,
} from "./bottom-sheet";

function Popover({ ...props }: React.ComponentProps<typeof PopoverPrimitive.Root>) {
	const touch = useTouch();
	if (touch) {
		const { open, defaultOpen, onOpenChange, children } = props;
		return (
			<BottomSheet open={open} defaultOpen={defaultOpen} onOpenChange={onOpenChange}>
				{children}
			</BottomSheet>
		);
	}
	return <PopoverPrimitive.Root data-slot="popover" {...props} />;
}

function PopoverTrigger({ ...props }: React.ComponentProps<typeof PopoverPrimitive.Trigger>) {
	const touch = useTouch();
	if (touch) return <BottomSheetTrigger data-slot="popover-trigger" {...props} />;
	return <PopoverPrimitive.Trigger data-slot="popover-trigger" {...props} />;
}

function PopoverAnchor({ ...props }: React.ComponentProps<typeof PopoverPrimitive.Anchor>) {
	const touch = useTouch();
	if (touch) {
		// Nothing to anchor to: a sheet sits at the bottom. The box stays.
		const { asChild, ...rest } = props;
		const Comp = asChild ? SlotPrimitive.Slot : "div";
		return <Comp data-slot="popover-anchor" {...rest} />;
	}
	return <PopoverPrimitive.Anchor data-slot="popover-anchor" {...props} />;
}

function PopoverClose({ ...props }: React.ComponentProps<typeof PopoverPrimitive.Close>) {
	const touch = useTouch();
	if (touch) return <BottomSheetClose data-slot="popover-close" {...props} />;
	return <PopoverPrimitive.Close data-slot="popover-close" {...props} />;
}

function PopoverArrow({
	className,
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Arrow>) {
	const touch = useTouch();
	if (touch) return null;
	return (
		<PopoverPrimitive.Arrow
			data-slot="popover-arrow"
			className={cn("fill-bg-elevated", className)}
			{...props}
		/>
	);
}

type PopoverContentProps = React.ComponentProps<typeof PopoverPrimitive.Content> & {
	/** Portal into this element rather than the body (or a full screen surface). */
	container?: HTMLElement | null;
};

function PopoverContent({
	className,
	align = "center",
	sideOffset = 4,
	container,
	...props
}: PopoverContentProps) {
	const touch = useTouch();
	const portal = usePortalContainer(container);
	if (touch) {
		// Placement means nothing at the bottom of the screen. The caller's
		// classes style the body, its width yields to the sheet's.
		const {
			side: _side,
			alignOffset: _alignOffset,
			avoidCollisions: _avoidCollisions,
			collisionBoundary: _collisionBoundary,
			collisionPadding: _collisionPadding,
			arrowPadding: _arrowPadding,
			sticky: _sticky,
			hideWhenDetached: _hideWhenDetached,
			updatePositionStrategy: _updatePositionStrategy,
			forceMount: _forceMount,
			children,
			...rest
		} = props;
		return (
			<BottomSheetContent
				container={portal}
				label={rest["aria-label"] ?? "Popover"}
				bodyClassName={cn(className, "w-full max-w-none")}
				{...rest}
			>
				{children}
			</BottomSheetContent>
		);
	}
	return (
		<PopoverPrimitive.Portal container={portal}>
			<PopoverPrimitive.Content
				data-slot="popover-content"
				align={align}
				sideOffset={sideOffset}
				className={cn(
					"z-50 w-72 p-3 outline-hidden",
					"bg-bg-elevated text-text-primary border border-border-default rounded-md shadow-floating",
					// Motion tokens per motion.md §3 Popover.
					"data-[state=open]:animate-in data-[state=closed]:animate-out",
					"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
					"data-[state=open]:duration-base data-[state=closed]:duration-base",
					"data-[state=open]:ease-out data-[state=closed]:ease-in",
					// Slight y-shift per side, direction flipped so it always eases into place.
					"data-[side=top]:data-[state=open]:slide-in-from-bottom-1",
					"data-[side=bottom]:data-[state=open]:slide-in-from-top-1",
					"data-[side=left]:data-[state=open]:slide-in-from-right-1",
					"data-[side=right]:data-[state=open]:slide-in-from-left-1",
					className,
				)}
				{...props}
			/>
		</PopoverPrimitive.Portal>
	);
}

export { Popover, PopoverAnchor, PopoverArrow, PopoverClose, PopoverContent, PopoverTrigger };
