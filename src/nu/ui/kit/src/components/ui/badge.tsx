// Badge primitive. cva variants over kit semantic tokens.
//
// Variant map merges nudle's status pill palette (default / destructive /
// outline used by the connection indicator) with the token-based colors we
// want going forward (primary/secondary map to accent + accent-2, neutral
// for muted chips). Kept as one API so App.tsx and every BadgeRef renderer
// share the same primitive; individual ref renderers can be retuned onto
// this in Phase F.

import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const badgeVariants = cva(
	"inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium border w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 [&>svg]:pointer-events-none transition-[color,background-color,box-shadow]",
	{
		variants: {
			variant: {
				primary: "bg-accent-wash text-accent border-accent-line",
				secondary: "bg-accent-2-wash text-accent-2 border-accent-2-line",
				neutral: "bg-elevated text-fg-secondary border-border-subtle",
				outline: "bg-transparent text-fg-secondary border-border-default",
				// Legacy nudle status-pill variants. Retained so the App.tsx
				// connection indicator keeps working; retune in Phase F.
				default: "bg-accent text-accent-fg border-transparent",
				destructive: "bg-red-500 text-white border-transparent",
				ghost: "bg-transparent text-fg-secondary border-transparent",
				link: "bg-transparent text-accent border-transparent underline-offset-4 hover:underline",
			},
		},
		defaultVariants: {
			variant: "primary",
		},
	},
);

function Badge({
	className,
	variant,
	asChild = false,
	...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
	const Comp = asChild ? Slot.Root : "span";
	return (
		<Comp
			data-slot="badge"
			data-variant={variant}
			className={cn(badgeVariants({ variant }), className)}
			{...props}
		/>
	);
}

export { Badge, badgeVariants };
