import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";
import { cn, ringVariants } from "../../lib/utils";

// Square icon-only button. Shares Button's variant map but drops text sizing
// and locks side = height. See design/primitives.md §IconButton.
// aria-label is required by the type (§a11y.md §4) so screen readers get a
// name even when the icon is the only child.
const iconButtonVariants = cva(
	[
		"inline-flex items-center justify-center rounded-md",
		"cursor-default",
		"transition-colors duration-fast ease-out",
		"disabled:pointer-events-none disabled:opacity-50",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			variant: {
				default:
					"bg-accent text-accent-fg border border-transparent hover:bg-accent-hover active:bg-accent-soft",
				secondary:
					"bg-bg-elevated text-text-primary border border-border-default hover:bg-bg-sunken hover:border-border-strong",
				// Hover wash mixed from the text color, so it reads on any surface
				// in both themes (bg-elevated is white on a white surface in light).
				// Rests muted: a lone glyph needs less weight than a text label.
				ghost:
					"bg-transparent text-text-muted border border-transparent hover:bg-text-primary/8 hover:text-text-primary active:bg-text-primary/12",
				outline:
					"bg-transparent text-text-primary border border-border-default hover:bg-bg-elevated hover:border-border-strong",
				// Ghost's wash held at rest, no border: a tile on a surface that
				// groups by fill rather than by line.
				soft: "bg-text-primary/6 text-text-muted border border-transparent hover:bg-text-primary/10 hover:text-text-primary active:bg-text-primary/14",
				destructive:
					"bg-status-danger text-status-danger-fg border border-transparent hover:bg-status-danger/90",
				// kept for parity with Button; primitives.md discourages link
				// styling on icon-only surfaces (no text to underline).
				link: "bg-transparent text-accent border border-transparent hover:opacity-80",
			},
			size: {
				xs: "size-5 rounded-sm [&_svg]:size-3",
				sm: "size-6 [&_svg]:size-3.5",
				md: "size-8 [&_svg]:size-4",
				lg: "size-10 [&_svg]:size-4.5",
			},
			ring: ringVariants,
		},
		defaultVariants: {
			variant: "default",
			size: "md",
			ring: "offset",
		},
	},
);

export interface IconButtonProps
	extends React.ComponentProps<"button">,
		VariantProps<typeof iconButtonVariants> {
	asChild?: boolean;
	"aria-label": string;
}

export function IconButton({
	className,
	variant,
	size,
	ring,
	asChild = false,
	...props
}: IconButtonProps) {
	const Comp = asChild ? SlotPrimitive.Root : "button";
	return (
		<Comp
			data-slot="icon-button"
			className={cn(iconButtonVariants({ variant, size, ring, className }))}
			{...props}
		/>
	);
}

export { iconButtonVariants };
