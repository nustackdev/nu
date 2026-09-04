import { cva, type VariantProps } from "class-variance-authority";
import { Toggle as TogglePrimitive } from "radix-ui";
import type * as React from "react";
import { cn } from "../../lib/utils";

// Two-state on/off button. Radix's Toggle exposes `data-state="on|off"` so
// the styling attaches through variant selectors (design/primitives.md
// §Toggle + motion.md §3 Toggle). Sizes track IconButton so a toolbar can
// mix them without row wobble.
const toggleVariants = cva(
	[
		"inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium",
		"cursor-pointer",
		"transition-colors duration-fast ease-out",
		"disabled:pointer-events-none disabled:opacity-50",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"[&_svg]:pointer-events-none [&_svg]:shrink-0",
		"text-text-secondary hover:bg-bg-elevated hover:text-text-primary",
		"data-[state=on]:bg-accent-wash data-[state=on]:text-text-primary",
	].join(" "),
	{
		variants: {
			variant: {
				default: "bg-transparent border border-transparent",
				outline:
					"bg-transparent border border-border-default hover:border-border-strong",
			},
			size: {
				sm: "h-6 min-w-6 px-1.5 text-sm [&_svg]:size-3.5",
				md: "h-8 min-w-8 px-2 text-lg [&_svg]:size-4",
				lg: "h-10 min-w-10 px-3 text-xl [&_svg]:size-4.5",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

export interface ToggleProps
	extends React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root>,
		VariantProps<typeof toggleVariants> {}

export function Toggle({
	className,
	variant,
	size,
	...props
}: ToggleProps) {
	return (
		<TogglePrimitive.Root
			data-slot="toggle"
			className={cn(toggleVariants({ variant, size, className }))}
			{...props}
		/>
	);
}

export { toggleVariants };
