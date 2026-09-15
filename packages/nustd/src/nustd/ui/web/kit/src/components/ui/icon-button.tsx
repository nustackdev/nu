import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";
import { cn } from "../../lib/utils";

// Square icon-only button. Shares Button's variant map but drops text sizing
// and locks side = height. See design/primitives.md §IconButton.
// aria-label is required by the type (§a11y.md §4) so screen readers get a
// name even when the icon is the only child.
const iconButtonVariants = cva(
	[
		"inline-flex items-center justify-center rounded-md",
		"cursor-pointer",
		"transition-colors duration-fast ease-out",
		"disabled:pointer-events-none disabled:opacity-50",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			variant: {
				default:
					"bg-accent text-accent-fg border border-transparent hover:bg-accent-hover active:bg-accent-soft",
				secondary:
					"bg-bg-elevated text-text-primary border border-border-default hover:bg-bg-sunken hover:border-border-strong",
				ghost:
					"bg-transparent text-text-secondary border border-transparent hover:bg-bg-elevated hover:text-text-primary",
				outline:
					"bg-transparent text-text-primary border border-border-default hover:bg-bg-elevated hover:border-border-strong",
				destructive:
					"bg-status-danger text-status-danger-fg border border-transparent hover:bg-status-danger/90",
				// kept for parity with Button; primitives.md discourages link
				// styling on icon-only surfaces (no text to underline).
				link: "bg-transparent text-accent border border-transparent hover:opacity-80",
			},
			size: {
				sm: "size-6 [&_svg]:size-3.5",
				md: "size-8 [&_svg]:size-4",
				lg: "size-10 [&_svg]:size-4.5",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

export interface IconButtonProps
	extends React.ButtonHTMLAttributes<HTMLButtonElement>,
		VariantProps<typeof iconButtonVariants> {
	asChild?: boolean;
	"aria-label": string;
}

export function IconButton({
	className,
	variant,
	size,
	asChild = false,
	...props
}: IconButtonProps) {
	const Comp = asChild ? SlotPrimitive.Root : "button";
	return (
		<Comp
			data-slot="icon-button"
			className={cn(iconButtonVariants({ variant, size, className }))}
			{...props}
		/>
	);
}

export { iconButtonVariants };
