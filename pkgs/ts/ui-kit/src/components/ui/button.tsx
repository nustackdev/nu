import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";
import { cn, ringVariants } from "../../lib/utils";

// Base + variants per design/primitives.md §Button.
// Motion tokens: transition-colors duration-fast ease-out (motion.md §3).
// Focus ring: 2px ring-ring, 2px offset from bg-canvas or inset (`ring`, a11y.md §1).
// Sizes: 24 / 32 / 40 row heights (space-radius.md §4 Button), plus a 20px
// `xs` for controls tucked inside a dense row (a tree's fold chevron).
const buttonVariants = cva(
	[
		"inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium",
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
				ghost:
					"bg-transparent text-text-secondary border border-transparent hover:bg-bg-hover hover:text-text-primary active:bg-bg-press",
				outline:
					"bg-transparent text-text-primary border border-border-default hover:bg-bg-hover hover:border-border-strong active:bg-bg-press",
				// Ghost's hover step held at rest, no border.
				soft: "bg-bg-hover text-text-secondary border border-transparent hover:bg-bg-press hover:text-text-primary active:bg-bg-press-strong",
				destructive:
					"bg-status-danger-solid text-text-inverse border border-transparent hover:bg-status-danger-solid-hover active:bg-status-danger-solid-pressed",
				// `link` ignores size (per primitives.md); pad + height zeroed so
				// it inlines with the surrounding text.
				link: "bg-transparent text-accent-text border border-transparent underline-offset-4 hover:underline p-0 h-auto",
			},
			size: {
				xs: "h-5 px-1.5 text-xs gap-1 [&_svg]:size-3.5",
				sm: "h-6 px-2 py-1 text-sm [&_svg]:size-3.5",
				md: "h-8 px-3 py-1.5 text-lg [&_svg]:size-4",
				lg: "h-10 px-4 py-2 text-xl [&_svg]:size-4.5",
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

export interface ButtonProps
	extends React.ComponentProps<"button">,
		VariantProps<typeof buttonVariants> {
	asChild?: boolean;
}

// No forwardRef: React 19 passes `ref` as a normal prop through Slot / <button>.
export function Button({
	className,
	variant,
	size,
	ring,
	asChild = false,
	...props
}: ButtonProps) {
	const Comp = asChild ? SlotPrimitive.Root : "button";
	return (
		<Comp
			data-slot="button"
			className={cn(buttonVariants({ variant, size, ring, className }))}
			{...props}
		/>
	);
}

export { buttonVariants };
