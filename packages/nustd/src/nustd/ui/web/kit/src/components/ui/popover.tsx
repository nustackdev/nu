// Popover primitive: anchored floating content, not focus-trapping.
// Design refs:
//   primitives.md    §Popover (parts, motion)
//   palette.md       §2.1 backgrounds, §2.3 borders
//   space-radius.md  §Density Popover (pad 12, radius `md`)
//   motion.md        §3 Popover (`duration-base` fade+y-shift)
//   a11y.md          §3 Popover (Esc, focus restore, no trap)

import { Popover as PopoverPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

function Popover({
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Root>) {
	return <PopoverPrimitive.Root data-slot="popover" {...props} />;
}

function PopoverTrigger({
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Trigger>) {
	return <PopoverPrimitive.Trigger data-slot="popover-trigger" {...props} />;
}

function PopoverAnchor({
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Anchor>) {
	return <PopoverPrimitive.Anchor data-slot="popover-anchor" {...props} />;
}

function PopoverClose({
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Close>) {
	return <PopoverPrimitive.Close data-slot="popover-close" {...props} />;
}

function PopoverArrow({
	className,
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Arrow>) {
	return (
		<PopoverPrimitive.Arrow
			data-slot="popover-arrow"
			className={cn("fill-bg-surface", className)}
			{...props}
		/>
	);
}

function PopoverContent({
	className,
	align = "center",
	sideOffset = 4,
	...props
}: React.ComponentProps<typeof PopoverPrimitive.Content>) {
	return (
		<PopoverPrimitive.Portal>
			<PopoverPrimitive.Content
				data-slot="popover-content"
				align={align}
				sideOffset={sideOffset}
				className={cn(
					"z-50 w-72 p-3 outline-hidden",
					"bg-bg-surface text-text-primary border border-border-subtle rounded-md shadow-lg",
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

export {
	Popover,
	PopoverTrigger,
	PopoverContent,
	PopoverAnchor,
	PopoverArrow,
	PopoverClose,
};
