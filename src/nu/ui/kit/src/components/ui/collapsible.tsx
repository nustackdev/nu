// Collapsible primitive. Wraps @radix-ui/react-collapsible.
// Design refs:
//   primitives.md    §Collapsible (thin wrapper, applies kit motion tokens)
//   motion.md        §3 Collapsible (content height base + ease-in-out)
//   a11y.md          §3 Collapsible (Radix wires Tab + Space/Enter)
//
// Simpler than Accordion: no roving focus, no group, single toggleable region.
// Content height animation rides Radix's --radix-collapsible-content-height.

import { Collapsible as CollapsiblePrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

export function Collapsible({
	...props
}: React.ComponentProps<typeof CollapsiblePrimitive.Root>) {
	return <CollapsiblePrimitive.Root data-slot="collapsible" {...props} />;
}

export function CollapsibleTrigger({
	...props
}: React.ComponentProps<typeof CollapsiblePrimitive.Trigger>) {
	return (
		<CollapsiblePrimitive.Trigger
			data-slot="collapsible-trigger"
			{...props}
		/>
	);
}

export function CollapsibleContent({
	className,
	...props
}: React.ComponentProps<typeof CollapsiblePrimitive.Content>) {
	return (
		<CollapsiblePrimitive.Content
			data-slot="collapsible-content"
			className={cn(
				"overflow-hidden",
				"data-[state=open]:animate-collapsible-down",
				"data-[state=closed]:animate-collapsible-up",
				className,
			)}
			{...props}
		/>
	);
}
