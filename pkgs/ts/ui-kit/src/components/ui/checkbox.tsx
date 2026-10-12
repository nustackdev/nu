import { cva, type VariantProps } from "class-variance-authority";
import { Minus } from "lucide-react";
import { Checkbox as CheckboxPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const checkboxVariants = cva(
	[
		"group peer inline-flex shrink-0 items-center justify-center rounded-sm",
		"border border-border-default bg-bg-surface text-accent-fg",
		"cursor-default",
		"transition-colors duration-fast ease-out",
		"hover:border-border-strong",
		"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
		// unticked press: the press wash laid over the box's own fill, so it
		// stacks like every other surface's
		"data-[state=unchecked]:active:border-border-strong",
		"data-[state=unchecked]:active:bg-[linear-gradient(var(--bg-press),var(--bg-press))]",
		// ticked: the accent, a step deeper on hover and press, like a primary button
		"data-[state=checked]:bg-accent data-[state=checked]:border-accent",
		"data-[state=checked]:hover:bg-accent-hover data-[state=checked]:hover:border-accent-hover",
		"data-[state=checked]:active:bg-accent-pressed data-[state=checked]:active:border-accent-pressed",
		"data-[state=indeterminate]:bg-accent data-[state=indeterminate]:border-accent",
		"data-[state=indeterminate]:hover:bg-accent-hover data-[state=indeterminate]:hover:border-accent-hover",
		"data-[state=indeterminate]:active:bg-accent-pressed data-[state=indeterminate]:active:border-accent-pressed",
		"aria-invalid:border-status-danger",
	].join(" "),
	{
		variants: {
			size: {
				sm: "size-[14px]",
				md: "size-4",
				lg: "size-5",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

export interface CheckboxProps
	extends Omit<React.ComponentProps<typeof CheckboxPrimitive.Root>, "size">,
		VariantProps<typeof checkboxVariants> {
	invalid?: boolean;
}

// The kit's own tick: a short left leg and a long right one, optically
// centred in the box, round ends. Lighter than a stock check at small sizes.
function Tick({ className }: { className?: string }) {
	return (
		<svg
			viewBox="0 0 16 16"
			fill="none"
			stroke="currentColor"
			strokeWidth={2.25}
			strokeLinecap="round"
			strokeLinejoin="round"
			aria-hidden="true"
			className={className}
		>
			<path d="M4 8.4 6.7 11 12 5.2" />
		</svg>
	);
}

export function Checkbox({ className, size, invalid, ...props }: CheckboxProps) {
	return (
		<CheckboxPrimitive.Root
			data-slot="checkbox"
			aria-invalid={invalid || undefined}
			className={cn(checkboxVariants({ size }), className)}
			{...props}
		>
			<CheckboxPrimitive.Indicator
				data-slot="checkbox-indicator"
				className="flex items-center justify-center"
			>
				{/* group-data on the Root reads Radix's data-state so the correct
				    glyph shows for checked vs indeterminate without extra state.
				    The glyphs paint with their own stroke, not currentColor: a
				    row that recolors its svgs (a command item) must not reach
				    the tick. */}
				<Tick className="size-full stroke-accent-fg group-data-[state=indeterminate]:hidden" />
				<Minus
					strokeWidth={3}
					className="hidden size-full stroke-accent-fg group-data-[state=indeterminate]:block"
				/>
			</CheckboxPrimitive.Indicator>
		</CheckboxPrimitive.Root>
	);
}

export { checkboxVariants };
