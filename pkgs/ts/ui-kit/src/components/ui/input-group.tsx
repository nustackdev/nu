// InputGroup: a field and the buttons that act on it, on one line.
//
// The line every "type, then press" form has: a search box and Search, a
// chat box and Send, a name and Create. The group does the two things a plain
// row leaves to the caller: the field takes the width the buttons leave, and
// the buttons sit on the field's bottom edge, so a field with its label above
// lines its box up with the buttons beside it. Gap 8px (2), the small gap
// between controls that belong together (space-radius.md).
//
// Which child grows: every child marked `data-fill`, or the first child when
// none is. Everything else keeps its own width and never shrinks below it.
//
// Help or an error under the field would push the field's box above the
// buttons' line: put the Field around the group, not inside it.

import type * as React from "react";
import { cn } from "../../lib/utils";

export function InputGroup({ className, ...props }: React.ComponentProps<"div">) {
	return (
		<div
			data-slot="input-group"
			className={cn(
				"flex min-w-0 flex-row flex-nowrap items-end gap-2",
				"*:shrink-0",
				"[&>[data-fill]]:min-w-0 [&>[data-fill]]:flex-1 [&>[data-fill]]:shrink",
				"[&:not(:has(>[data-fill]))>:first-child]:min-w-0 [&:not(:has(>[data-fill]))>:first-child]:flex-1 [&:not(:has(>[data-fill]))>:first-child]:shrink",
				className,
			)}
			{...props}
		/>
	);
}
