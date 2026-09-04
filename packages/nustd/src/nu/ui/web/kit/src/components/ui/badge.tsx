// Badge primitive.
//
// cva over kit semantic tokens. Status variants pair color with icon/dot per
// a11y.md §7 (color is never the only signal); consumer supplies the glyph.

import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const badgeVariants = cva(
	[
		"inline-flex items-center gap-1 whitespace-nowrap w-fit shrink-0 border",
		"font-display font-medium tracking-[0.01em] leading-none",
		"[&>svg]:pointer-events-none [&>svg]:shrink-0",
		"transition-colors duration-fast ease-out",
	].join(" "),
	{
		variants: {
			variant: {
				// Accent purple wash. Default identity chip.
				default: "bg-accent-wash text-accent border-accent-line",
				// Blue secondary wash.
				secondary: "bg-accent-2-wash text-accent-2 border-accent-2-line",
				// Transparent bg with muted border for neutral labels.
				outline: "bg-transparent text-text-secondary border-border-default",
				// Status hues.
				danger: "bg-status-danger-wash text-status-danger border-status-danger-line",
				warn: "bg-status-warn-wash text-status-warn border-status-warn-line",
				ok: "bg-status-ok-wash text-status-ok border-status-ok-line",
				info: "bg-status-info-wash text-status-info border-status-info-line",
			},
			size: {
				sm: "text-xs px-1.5 py-0.5 rounded-sm [&>svg]:size-3",
				md: "text-xs px-2 py-0.5 rounded-sm [&>svg]:size-3",
				lg: "text-sm px-2.5 py-1 rounded-md [&>svg]:size-3.5",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

export interface BadgeProps
	extends React.HTMLAttributes<HTMLSpanElement>,
		VariantProps<typeof badgeVariants> {
	asChild?: boolean;
}

function Badge({ className, variant, size, asChild = false, ...props }: BadgeProps) {
	const Comp = asChild ? Slot.Root : "span";
	return (
		<Comp
			data-slot="badge"
			className={cn(badgeVariants({ variant, size }), className)}
			{...props}
		/>
	);
}

export { Badge, badgeVariants };
