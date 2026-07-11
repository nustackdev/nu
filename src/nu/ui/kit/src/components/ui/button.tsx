import { cva, type VariantProps } from "class-variance-authority";
import { Slot as SlotPrimitive } from "radix-ui";
import type * as React from "react";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
	[
		"inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium",
		"transition-[background-color,border-color,color,box-shadow] duration-150",
		"disabled:pointer-events-none disabled:opacity-50",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
		"focus-visible:ring-offset-canvas",
		"[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			variant: {
				primary:
					"bg-accent text-accent-fg hover:bg-accent-hover border border-transparent",
				secondary:
					"bg-accent-2 text-accent-2-fg hover:bg-accent-2-hover border border-transparent",
				soft: "bg-accent-wash text-fg border border-accent-line hover:bg-accent-soft",
				outline:
					"bg-transparent text-fg border border-border-default hover:bg-elevated hover:border-border-strong",
				ghost: "bg-transparent text-fg-secondary hover:bg-elevated hover:text-fg border border-transparent",
				link: "bg-transparent text-accent underline-offset-4 hover:underline p-0 h-auto",
			},
			size: {
				sm: "h-8 px-3 text-xs",
				md: "h-9 px-4 text-sm",
				lg: "h-11 px-6 text-base",
				icon: "h-9 w-9",
			},
		},
		defaultVariants: {
			variant: "primary",
			size: "md",
		},
	},
);

export interface ButtonProps
	extends React.ButtonHTMLAttributes<HTMLButtonElement>,
		VariantProps<typeof buttonVariants> {
	asChild?: boolean;
}

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
			className={cn(buttonVariants({ variant, size, className }))}
			{...props}
		/>
	);
}

export { buttonVariants };
