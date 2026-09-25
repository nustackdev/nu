// Tooltip primitive: hover/focus hint anchored to a trigger.
// Design refs:
//   primitives.md    §Tooltip (parts, sizes, motion)
//   palette.md       §2.1 backgrounds (bg-bg-elevated)
//   space-radius.md  §Density Tooltip (pad 4x8, radius `sm`, text-xs)
//   motion.md        §3 Tooltip (`duration-base` fade+scale-96)
//   a11y.md          §3 Tooltip (trigger-focus opens, Esc dismisses)
//
// Kit overrides the Radix 300ms default to 200ms (primitives.md §Tooltip);
// mount TooltipProvider once near the app root.

import { Tooltip as TooltipPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

// Content box geometry, for OverflowTooltip to size a tooltip before it opens.
// Kept in step with TooltipContent's classes: px-2 plus a 1px border a side,
// max-w-xs, and the default side offset.
export const TOOLTIP_CHROME_PX = 18;
export const TOOLTIP_MAX_PX = 320;
export const TOOLTIP_SIDE_OFFSET = 4;

function TooltipProvider({
	delayDuration = 800,
	skipDelayDuration = 300,
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Provider>) {
	return (
		<TooltipPrimitive.Provider
			data-slot="tooltip-provider"
			delayDuration={delayDuration}
			skipDelayDuration={skipDelayDuration}
			{...props}
		/>
	);
}

function Tooltip({
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Root>) {
	return <TooltipPrimitive.Root data-slot="tooltip" {...props} />;
}

function TooltipTrigger({
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Trigger>) {
	return <TooltipPrimitive.Trigger data-slot="tooltip-trigger" {...props} />;
}

function TooltipContent({
	className,
	sideOffset = TOOLTIP_SIDE_OFFSET,
	children,
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Content>) {
	return (
		<TooltipPrimitive.Portal>
			<TooltipPrimitive.Content
				data-slot="tooltip-content"
				sideOffset={sideOffset}
				className={cn(
					"z-50 max-w-xs px-2 py-1 rounded-sm",
					"bg-bg-elevated text-text-primary border border-border-subtle shadow-sm",
					"text-xs leading-tight",
					"data-[state=delayed-open]:animate-in data-[state=closed]:animate-out",
					"data-[state=delayed-open]:fade-in-0 data-[state=closed]:fade-out-0",
					"data-[state=delayed-open]:zoom-in-95 data-[state=closed]:zoom-out-95",
					"data-[state=delayed-open]:duration-base data-[state=closed]:duration-base",
					"data-[state=delayed-open]:ease-out data-[state=closed]:ease-in",
					className,
				)}
				{...props}
			>
				{children}
			</TooltipPrimitive.Content>
		</TooltipPrimitive.Portal>
	);
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
