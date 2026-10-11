// Grid primitive. STUB: a plain wrapper so the Grid node has something to
// compose; the grid unit replaces it with the real column and gap rules
// (design/systems/kit) and its stories.
//
// Equal cells, row after row. No outer margin: a grid placed in a layout is
// spaced by that layout.

import type * as React from "react";
import { cn } from "../../lib/utils";

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Grid({ className, ...props }: GridProps) {
	return <div data-slot="grid" className={cn("grid grid-cols-1 gap-4", className)} {...props} />;
}
