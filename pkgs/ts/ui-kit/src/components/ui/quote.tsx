// Quote primitive. A header line over a body, set apart as quoted.
// Design refs:
//   palette.md       accent-line (accent borders), text-secondary
//   space-radius.md  pad 12 off the rule, 4 between header and body
//   typography.md    text-sm header, weight for emphasis, never ornament
//
// The look markdown gives a blockquote (`prose.tsx`): a 2px Afterglow line
// down the left edge and quieter ink. Afterglow marks the place as a line,
// never a fill. Inside, the primary ink role is rebound to the secondary
// one, the way `.on-media` rebinds roles, so whatever sits in it (a Text,
// markdown, a heading) reads one step quieter with no prop of its own,
// while an explicit tone (muted, danger, ...) keeps its color.
//
// The header box takes the full width and lets its child shrink, so a row
// that truncates inside it can. How the header looks is its child's business.

import type * as React from "react";

import { cn } from "../../lib/utils";

export function Quote({ className, ...props }: React.ComponentProps<"div">) {
	return (
		<div
			data-slot="quote"
			className={cn(
				"flex min-w-0 flex-col gap-1 border-l-2 border-accent-line pl-3",
				"text-text-secondary [--text-primary:var(--text-secondary)]",
				className,
			)}
			{...props}
		/>
	);
}

export function QuoteHeader({ className, ...props }: React.ComponentProps<"div">) {
	return (
		<div
			data-slot="quote-header"
			className={cn("flex w-full min-w-0 flex-col text-sm font-medium", className)}
			{...props}
		/>
	);
}

export function QuoteContent({ className, ...props }: React.ComponentProps<"div">) {
	return (
		<div
			data-slot="quote-content"
			className={cn("flex min-w-0 flex-col gap-2", className)}
			{...props}
		/>
	);
}
