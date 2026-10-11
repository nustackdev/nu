// Line primitive. STUB: a plain wrapper so the Line node has something to
// compose; the line unit replaces it with the real inline rhythm (baseline,
// word spacing, wrapping) and its stories.
//
// Children run inline and wrap like words in a paragraph: text runs, links,
// badges, keys. No outer margin.

import type * as React from "react";
import { cn } from "../../lib/utils";

export interface LineProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Line({ className, ...props }: LineProps) {
	return (
		<div
			data-slot="line"
			className={cn("flex flex-wrap items-baseline gap-x-1", className)}
			{...props}
		/>
	);
}
