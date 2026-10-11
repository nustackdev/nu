// Line primitive. Children run inline and wrap like words in a paragraph:
// text runs, links, badges, keys, shortcuts, status dots in one sentence.
//
// Real inline layout, not a flex row: the box is a block, its children are
// inline boxes, so a long text run breaks mid-run at the box's edge and the
// next run picks up after it on the same line. Every child is followed by
// one space (`LineRun`), the word space of the body face, which collapses
// at the start and end of a line the way any space in a paragraph does, so
// a wrapped line never starts indented and the runs can break between
// items. A lone child gets none: the Line node hands its children over as
// one and puts `LineRun` on each itself.
//
// Type is the kit body (design/systems/kit/typography.md "Body prose":
// base, 400, text-primary), with a 24px line box instead of 1.5: a key cap
// is 20px tall and a badge 17px, and a line box that holds them with room
// to spare keeps every wrapped line the same height, on the 4px grid
// (design/language/space-radius.md). The box carries the same 4px of
// vertical padding as Text and Prose, padding never margin.
//
// Chips sit on the text's baseline (`lineChip`): an inline-flex box's
// baseline is its own text's, so a badge's label and a key's glyph line up
// with the words around them. A dot has no text, so it centers on the
// x-height instead (`lineDot`).
//
// `wrap={false}` keeps one line: the end clips, with an ellipsis when the
// cut falls in text.

import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "../../lib/utils";

const lineVariants = cva(
	"block min-w-0 py-1 font-display font-normal text-base text-text-primary leading-6",
	{
		variants: {
			align: {
				start: "text-start",
				center: "text-center",
				end: "text-end",
			},
			wrap: {
				true: "whitespace-normal [overflow-wrap:anywhere]",
				false: "overflow-hidden text-ellipsis whitespace-nowrap",
			},
		},
		defaultVariants: {
			align: "start",
			wrap: true,
		},
	},
);

/** Classes a chip (badge, key, shortcut) takes to sit on the text's baseline in a Line. */
export const lineChip = "inline-flex align-baseline";

/** Classes a dot takes to sit centered on the x-height in a Line. */
export const lineDot = "inline-block align-middle";

export interface LineProps
	extends React.HTMLAttributes<HTMLDivElement>,
		VariantProps<typeof lineVariants> {}

/** One child of a Line, followed by the word space that separates it from the next. */
export function LineRun({ children }: { children?: React.ReactNode }) {
	return <>{children} </>;
}

export function Line({ className, align, wrap, children, ...props }: LineProps) {
	return (
		<div
			data-slot="line"
			data-wrap={wrap === false ? "false" : "true"}
			className={cn(lineVariants({ align, wrap }), className)}
			{...props}
		>
			{React.Children.count(children) < 2
				? children
				: React.Children.map(children, (child) =>
						child == null || typeof child === "boolean" ? null : <LineRun>{child}</LineRun>,
					)}
		</div>
	);
}

export { lineVariants };
