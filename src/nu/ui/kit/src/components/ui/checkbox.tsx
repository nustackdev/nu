import { cva, type VariantProps } from "class-variance-authority";
import { Check, Minus } from "lucide-react";
import { Checkbox as CheckboxPrimitive } from "radix-ui";
import type * as React from "react";

import { cn } from "../../lib/utils";

const checkboxVariants = cva(
	[
		"group peer inline-flex shrink-0 items-center justify-center rounded-sm",
		"border border-border-default bg-bg-surface text-accent-fg",
		"transition-colors duration-fast ease-out",
		"hover:border-border-strong",
		"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
		"data-[state=checked]:bg-accent data-[state=checked]:border-accent",
		"data-[state=indeterminate]:bg-accent data-[state=indeterminate]:border-accent",
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
				    glyph shows for checked vs indeterminate without extra state. */}
				<Check
					strokeWidth={3}
					className="size-full group-data-[state=indeterminate]:hidden"
				/>
				<Minus
					strokeWidth={3}
					className="hidden size-full group-data-[state=indeterminate]:block"
				/>
			</CheckboxPrimitive.Indicator>
		</CheckboxPrimitive.Root>
	);
}

export { checkboxVariants };
