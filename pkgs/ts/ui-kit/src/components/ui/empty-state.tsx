// EmptyState primitive. What a region says when it has nothing to show yet:
// an empty list, a missing record, a load in flight.
//
// Muted and centered, never a card: it stands in for content, so it takes no
// surface of its own. The children are the one line that says what is missing;
// `description` is a smaller line under it, `icon` sits above (a lucide glyph,
// or a Spinner for a load, which keeps its own status role), and `action` is
// the way out under both.
// `sm` fits a sidebar or a menu, `md` a pane or a page section.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "../../lib/utils";

const emptyStateVariants = cva(
	[
		"flex flex-col items-center justify-center text-center text-text-muted select-none",
		"[&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			size: {
				sm: "gap-1 px-3 py-3 text-sm [&_svg]:size-4",
				md: "gap-2 px-4 py-8 text-base [&_svg]:size-5",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

export interface EmptyStateProps
	extends React.ComponentProps<"div">,
		VariantProps<typeof emptyStateVariants> {
	icon?: React.ReactNode;
	description?: React.ReactNode;
	action?: React.ReactNode;
}

export function EmptyState({
	className,
	size,
	icon,
	description,
	action,
	children,
	...props
}: EmptyStateProps) {
	return (
		<div data-slot="empty-state" className={cn(emptyStateVariants({ size }), className)} {...props}>
			{icon ? <span className="flex">{icon}</span> : null}
			{children ? <p>{children}</p> : null}
			{description ? <p className="text-xs">{description}</p> : null}
			{action ? <div className="mt-1">{action}</div> : null}
		</div>
	);
}

export { emptyStateVariants };
