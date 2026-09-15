import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";
import { cn } from "../../lib/utils";

// Base + variants per design/primitives.md §Button.
// Motion tokens: transition-colors duration-fast ease-out (motion.md §3).
// Focus ring: 2px ring-ring, 2px offset from bg-canvas (a11y.md §1).
// Sizes: 24 / 32 / 40 row heights (space-radius.md §4 Button).
const buttonVariants = cva(
	[
		"inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium",
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
				// `link` ignores size (per primitives.md); pad + height zeroed so
				// it inlines with the surrounding text.
				link: "bg-transparent text-accent border border-transparent underline-offset-4 hover:underline p-0 h-auto",
			},
			size: {
				sm: "h-6 px-2 py-1 text-sm [&_svg]:size-3.5",
				md: "h-8 px-3 py-1.5 text-lg [&_svg]:size-4",
				lg: "h-10 px-4 py-2 text-xl [&_svg]:size-4.5",
			},
		},
		defaultVariants: {
			variant: "default",
			size: "md",
		},
	},
);

export interface ButtonProps
	extends React.ButtonHTMLAttributes<HTMLButtonElement>,
		VariantProps<typeof buttonVariants> {
	asChild?: boolean;
}

// No forwardRef: React 19 passes `ref` as a normal prop through Slot / <button>.
export function Button({
	className,
	variant,
	size,
	asChild = false,
	...props
}: ButtonProps) {
	const Comp = asChild ? SlotPrimitive.Root : "button";
	return (
		<Comp
			data-slot="button"
			className={cn(buttonVariants({ variant, size, className }))}
			{...props}
		/>
	);
}

export { buttonVariants };
