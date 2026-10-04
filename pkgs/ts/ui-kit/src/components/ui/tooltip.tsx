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
import * as React from "react";

import { cn } from "../../lib/utils";

// Content box geometry, for OverflowTooltip to size a tooltip before it opens.
// Kept in step with TooltipContent's classes: px-2 plus a 1px border a side,
// max-w-xs, and the default side offset.
export const TOOLTIP_CHROME_PX = 18;
export const TOOLTIP_MAX_PX = 320;
export const TOOLTIP_SIDE_OFFSET = 4;

// Kit tooltips are hints, never interactive, so their content is not
// hoverable. Radix's hoverable content keeps a tooltip open while the pointer
// crosses a grace area from the trigger toward the content, and counts the
// pointer as in transit meanwhile, which blocks every other trigger from
// opening. Under a row of adjacent controls with tooltips below them, that
// area covers the neighbours: moving from one control to the next leaves the
// first tooltip up and the next one shut until the pointer happens to leave
// the area. Not hoverable, leaving a trigger closes its tooltip, and the next
// one opens at once inside the skip window.
function TooltipProvider({
	delayDuration = 800,
	skipDelayDuration = 300,
	disableHoverableContent = true,
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Provider>) {
	return (
		<TooltipPrimitive.Provider
			data-slot="tooltip-provider"
			delayDuration={delayDuration}
			skipDelayDuration={skipDelayDuration}
			disableHoverableContent={disableHoverableContent}
			{...props}
		/>
	);
}

// Refusing to open, done before Radix starts its timer.
//
// A controlled tooltip that refuses in `onOpenChange` is too late: by then
// Radix has told the provider a tooltip opened, which turns off the delay for
// every tooltip under it, and since the refused one never closes the provider
// never starts the timer that turns it back on. Every tooltip after that opens
// instantly. `canOpen` is asked on the trigger's pointer move and focus
// instead, and a no cancels the event before Radix sees it, so a refused
// tooltip never starts opening and the provider is never told. Every refusal
// goes through it.
type CanOpen = (() => boolean) | undefined;
const CanOpenContext = React.createContext<CanOpen>(undefined);

function Tooltip({
	canOpen,
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Root> & {
	/** Asked before the tooltip starts opening; false keeps it shut. */
	canOpen?: () => boolean;
}) {
	return (
		<CanOpenContext.Provider value={canOpen}>
			<TooltipPrimitive.Root data-slot="tooltip" {...props} />
		</CanOpenContext.Provider>
	);
}

function TooltipTrigger({
	onPointerMove,
	onFocus,
	...props
}: React.ComponentProps<typeof TooltipPrimitive.Trigger>) {
	const canOpen = React.useContext(CanOpenContext);
	return (
		<TooltipPrimitive.Trigger
			data-slot="tooltip-trigger"
			onPointerMove={(e) => {
				onPointerMove?.(e);
				if (!e.defaultPrevented && canOpen && !canOpen()) e.preventDefault();
			}}
			onFocus={(e) => {
				onFocus?.(e);
				if (!e.defaultPrevented && canOpen && !canOpen()) e.preventDefault();
			}}
			{...props}
		/>
	);
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
