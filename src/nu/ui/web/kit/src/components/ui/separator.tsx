// Separator primitive.
//
// Radix Separator + optional label slot for horizontal dividers (per refs.md
// DividerRef gap). Labeled variant renders text centered with lines on both
// sides.

import { Separator as SeparatorPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

type SeparatorPrimitiveProps = React.ComponentProps<typeof SeparatorPrimitive.Root>;

export interface SeparatorProps extends SeparatorPrimitiveProps {
	label?: React.ReactNode;
}

function Separator({
	className,
	orientation = "horizontal",
	decorative = true,
	label,
	...props
}: SeparatorProps) {
	if (label && orientation === "horizontal") {
		// The Radix Separator sits under the label rail, split into two lines.
		// Aria still points at a single divider for screen readers.
		return (
			<div
				data-slot="separator-labeled"
				className={cn("flex items-center gap-3 w-full", className)}
				role={decorative ? "none" : undefined}
			>
				<div aria-hidden="true" className="flex-1 h-px bg-border-subtle" />
				<span className="text-xs text-text-secondary font-display shrink-0">
					{label}
				</span>
				<div aria-hidden="true" className="flex-1 h-px bg-border-subtle" />
			</div>
		);
	}

	return (
		<SeparatorPrimitive.Root
			data-slot="separator"
			decorative={decorative}
			orientation={orientation}
			className={cn(
				"shrink-0 bg-border-subtle",
				orientation === "horizontal" ? "h-px w-full" : "h-full w-px",
				className,
			)}
			{...props}
		/>
	);
}

export { Separator };
