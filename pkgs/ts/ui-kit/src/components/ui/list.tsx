import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { list } from "../../lib/recipes";
import { cn } from "../../lib/utils";

// A bulleted or numbered run of short items (design/primitives.md §List).
// Semantic `<ul>` / `<ol>`, so a screen reader announces a list and its
// length.
//
// Markers, 20px indent and 2px between items are the list recipe
// (lib/recipes.ts), which a markdown list in `Prose` (./prose.tsx) is drawn
// with too. The difference is the size: this sets the kit's text-base body,
// Prose its reading size a step up. So it sits with the dense text around it
// (a TextRef, a label), not with a document's prose. No outer margin: a list
// placed in a layout is spaced by that layout. Items take any content: text,
// a link, a badge.
const listVariants = cva([list.base, "font-display text-base leading-normal"].join(" "), {
	variants: {
		variant: {
			bullet: list.bullet,
			number: list.number,
		},
	},
	defaultVariants: {
		variant: "bullet",
	},
});

type ListVariant = NonNullable<VariantProps<typeof listVariants>["variant"]>;

export interface ListProps extends React.HTMLAttributes<HTMLElement> {
	variant?: ListVariant;
	/** The first number of a numbered list. Ignored on bullets. */
	start?: number;
}

export function List({ className, variant = "bullet", start, ...props }: ListProps) {
	const cls = cn(listVariants({ variant }), className);
	if (variant === "number") {
		return (
			<ol
				data-slot="list"
				start={start !== undefined && start !== 1 ? start : undefined}
				className={cls}
				{...(props as React.OlHTMLAttributes<HTMLOListElement>)}
			/>
		);
	}
	return (
		<ul data-slot="list" className={cls} {...(props as React.HTMLAttributes<HTMLUListElement>)} />
	);
}

export function ListItem({ className, ...props }: React.LiHTMLAttributes<HTMLLIElement>) {
	return <li data-slot="list-item" className={className} {...props} />;
}

export { type ListVariant, listVariants };
