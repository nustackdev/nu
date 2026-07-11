import { cva, type VariantProps } from "class-variance-authority";
import { Switch as SwitchPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const switchVariants = cva(
	[
		"peer inline-flex shrink-0 items-center rounded-full",
		"border border-transparent",
		"transition-colors duration-fast ease-out",
		"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
		"data-[state=unchecked]:bg-bg-sunken data-[state=unchecked]:border-border-default",
		"data-[state=checked]:bg-accent data-[state=checked]:border-accent",
		"hover:data-[state=unchecked]:border-border-strong",
	].join(" "),
	{
		variants: {
			size: {
				sm: "h-4 w-7",
				md: "h-5 w-9",
				lg: "h-6 w-11",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

const switchThumbVariants = cva(
	[
		"pointer-events-none block rounded-full",
		"bg-bg-surface data-[state=checked]:bg-accent-fg",
		"transition-transform duration-fast ease-out",
		"translate-x-0.5",
	].join(" "),
	{
		variants: {
			size: {
				// Track width - thumb size - (2 * 2px inset) = translate distance.
				// sm: 28 - 12 - 4 = 12 -> translate-x-3
				// md: 36 - 16 - 4 = 16 -> translate-x-4
				// lg: 44 - 20 - 4 = 20 -> translate-x-5
				sm: "size-3 data-[state=checked]:translate-x-3",
				md: "size-4 data-[state=checked]:translate-x-4",
				lg: "size-5 data-[state=checked]:translate-x-5",
			},
		},
		defaultVariants: {
			size: "md",
		},
	},
);

export interface SwitchProps
	extends Omit<React.ComponentProps<typeof SwitchPrimitive.Root>, "size">,
		VariantProps<typeof switchVariants> {}

export function Switch({ className, size, ...props }: SwitchProps) {
	return (
		<SwitchPrimitive.Root
			data-slot="switch"
			className={cn(switchVariants({ size }), className)}
			{...props}
		>
			<SwitchPrimitive.Thumb
				data-slot="switch-thumb"
				className={switchThumbVariants({ size })}
			/>
		</SwitchPrimitive.Root>
	);
}

export { switchVariants };
