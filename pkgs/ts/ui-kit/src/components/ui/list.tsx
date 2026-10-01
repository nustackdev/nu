import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "../../lib/utils";

// A bulleted or numbered run of short items (design/primitives.md §List).
// Semantic `<ul>` / `<ol>`, so a screen reader announces a list and its
// length.
//
// It draws a list the way `Prose` draws one written in markdown (./prose.tsx):
// same markers, same 20px indent, same 2px between items, same type. A list
// built from data and a list typed into a document are one thing to the
// reader. The one difference is the outer margin: none here, since a list
// placed in a layout is spaced by that layout. Items take any content: text,
// a link, a badge.
const listVariants = cva(
	[
		"pl-5 font-display text-base leading-normal text-text-primary",
		"[&>li]:my-0.5 [&>li:first-child]:mt-0 [&>li:last-child]:mb-0",
	].join(" "),
	{
		variants: {
			variant: {
				bullet: "list-disc",
				number: "list-decimal",
			},
		},
		defaultVariants: {
			variant: "bullet",
		},
	},
);

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

export { listVariants, type ListVariant };
