// Text primitive.
//
// Non-heading text block. Defaults to <p> so consumer flow reads as prose;
// override via `as` for span/div/label placement. Tone selects from the
// semantic ladder; mono flips to JetBrains Mono for code/data readouts.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { tone } from "../../lib/recipes";
import { cn } from "../../lib/utils";

const textVariants = cva("", {
	variants: {
		size: {
			xs: "text-xs",
			sm: "text-sm",
			base: "text-base",
			lg: "text-lg",
			xl: "text-xl",
		},
		// The kit's one tone ladder (lib/recipes.ts).
		tone,
		weight: {
			regular: "font-normal",
			medium: "font-medium",
			semibold: "font-semibold",
			bold: "font-bold",
		},
		mono: {
			true: "font-mono",
			false: "font-display",
		},
	},
	defaultVariants: {
		size: "base",
		tone: "primary",
		weight: "regular",
		mono: false,
	},
});

type TextTag = "p" | "span" | "div" | "label" | "small" | "strong" | "em";

export interface TextProps
	extends Omit<React.HTMLAttributes<HTMLElement>, "children">,
		VariantProps<typeof textVariants> {
	as?: TextTag;
	children?: React.ReactNode;
}

function Text({
	className,
	size,
	tone,
	weight,
	mono,
	as = "p",
	children,
	...props
}: TextProps) {
	const Comp = as;
	return (
		<Comp
			data-slot="text"
			className={cn(textVariants({ size, tone, weight, mono }), className)}
			{...props}
		>
			{children}
		</Comp>
	);
}

export { Text, textVariants };
