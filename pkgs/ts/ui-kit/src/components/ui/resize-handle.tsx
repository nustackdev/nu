import type * as React from "react";
import { resizeHandleClasses } from "../../lib/resize";
import { cn } from "../../lib/utils";

// The drag strip on a resizable column's edge. Pair it with
// `useResizableWidth`: the parent is `relative` and takes the width inline,
// the handle rides its `side` edge. A click or double-click snaps back to the
// default width.

export interface ResizeHandleProps extends React.ComponentProps<"div"> {
	side?: "left" | "right";
}

export function ResizeHandle({ side = "right", className, ...props }: ResizeHandleProps) {
	return (
		<div
			data-slot="resize-handle"
			role="separator"
			aria-orientation="vertical"
			aria-label="Resize"
			className={cn(resizeHandleClasses(side), className)}
			{...props}
		/>
	);
}
