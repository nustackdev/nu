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
					"bg-accent text-accent-fg border border-transparent hover:bg-accent-hover active:bg-accent-pressed",
				secondary:
					"bg-bg-elevated text-text-primary border border-border-default hover:bg-bg-elevated-hover hover:border-border-strong active:bg-bg-elevated-press",
				// Hover is the one ground step every surface shares (bg-hover).
				// Rests muted: a lone glyph needs less weight than a text label.
				ghost:
					"bg-transparent text-text-muted border border-transparent hover:bg-bg-hover hover:text-text-primary active:bg-bg-press",
				outline:
					"bg-transparent text-text-primary border border-border-default hover:bg-bg-hover hover:border-border-strong active:bg-bg-press",
				// Ghost's hover step held at rest, no border: a tile on a surface that
				// groups by fill rather than by line.
				soft: "bg-bg-hover text-text-muted border border-transparent hover:bg-bg-press hover:text-text-primary active:bg-bg-press-strong",
				destructive:
					"bg-status-danger-solid text-text-inverse border border-transparent hover:bg-status-danger-solid-hover active:bg-status-danger-solid-pressed",
				// kept for parity with Button; primitives.md discourages link
				// styling on icon-only surfaces (no text to underline).
				link: "bg-transparent text-accent-text border border-transparent hover:opacity-80",
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
