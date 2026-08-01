import { cva, type VariantProps } from "class-variance-authority";
import { RadioGroup as RadioGroupPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const radioGroupItemVariants = cva(
	[
		"aspect-square inline-flex shrink-0 items-center justify-center rounded-full",
		"border border-border-default bg-bg-surface",
		"cursor-pointer",
		"transition-colors duration-fast ease-out",
		"hover:border-border-strong",
		"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
		"data-[state=checked]:bg-accent data-[state=checked]:border-accent",
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

const radioIndicatorSizes = {
	sm: "size-1.5",
	md: "size-2",
	lg: "size-2.5",
} as const;

export function RadioGroup({
	className,
	...props
}: React.ComponentProps<typeof RadioGroupPrimitive.Root>) {
	return (
		<RadioGroupPrimitive.Root
			data-slot="radio-group"
			className={cn("grid gap-2", className)}
			{...props}
		/>
	);
}

export interface RadioGroupItemProps
	extends Omit<React.ComponentProps<typeof RadioGroupPrimitive.Item>, "size">,
		VariantProps<typeof radioGroupItemVariants> {
	invalid?: boolean;
}

export function RadioGroupItem({
	className,
	size,
	invalid,
	...props
}: RadioGroupItemProps) {
	const dotSize = radioIndicatorSizes[size ?? "md"];
	return (
		<RadioGroupPrimitive.Item
			data-slot="radio-group-item"
			aria-invalid={invalid || undefined}
			className={cn(radioGroupItemVariants({ size }), className)}
			{...props}
		>
			<RadioGroupPrimitive.Indicator
				data-slot="radio-group-indicator"
				className="flex items-center justify-center"
			>
				<span className={cn("rounded-full bg-accent-fg", dotSize)} />
			</RadioGroupPrimitive.Indicator>
		</RadioGroupPrimitive.Item>
	);
}

export { radioGroupItemVariants };
