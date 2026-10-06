// Heading primitive.
//
// Renders a real h1..h6 (semantic HTML) with typography per typography.md §4.
// `as` picks the tag; `size` decouples visual size from semantic level so a
// visual "section title" can still ship as an h2 or h3.

import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { heading } from "../../lib/recipes";
import { cn } from "../../lib/utils";

// The sizes are the heading recipe (lib/recipes.ts), which a markdown
// document's h1..h4 are drawn with too:
//   display -> h1 hero, 32/1.2/-0.02
//   3xl     -> h2 page title, 24/1.3/-0.015
//   2xl     -> h3 card/dialog title, 20/1.4/-0.01
//   xl      -> h4 subsection, 16/1.55/-0.006
//   lg      -> h5 label, 14/1.45/-0.003
const headingVariants = cva(heading.base, {
	variants: {
		size: heading.size,
	},
	defaultVariants: {
		size: "2xl",
	},
});

type HeadingTag = "h1" | "h2" | "h3" | "h4" | "h5" | "h6";

export interface HeadingProps
	extends Omit<React.HTMLAttributes<HTMLHeadingElement>, "children">,
		VariantProps<typeof headingVariants> {
	as?: HeadingTag;
	children?: React.ReactNode;
}

function Heading({ className, size, as = "h2", children, ...props }: HeadingProps) {
	const Comp = as;
	return (
		<Comp data-slot="heading" className={cn(headingVariants({ size }), className)} {...props}>
			{children}
		</Comp>
	);
}

export { Heading, headingVariants };
