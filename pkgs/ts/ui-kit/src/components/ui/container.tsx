// Container primitive. The page frame: full width up to a named cap, centred.
// Design refs:
//   space-radius.md  §3 container widths (the `--container-*` tokens)
//   space-radius.md  §1 spacing scale (gutter and gap steps)
//
// Fluid below the cap, so the width never jumps at a breakpoint. The one
// thing that follows the window is the side gutter: 16px on a phone, 32px
// from `md`, 48px from `lg`. `padding` (a space step, 0..16) replaces it with
// one step on every side, `padding={0}` for a page that runs edge to edge.
// Children stack down the frame with `gap` between them. The props are the
// wire's: `maxWidth` is `max_width`, `padding` is `padding`.
//
// Sizes are the theme's container tokens, spelled out so Tailwind sees every
// class. Prose reads its token by name: `max-w-prose` is Tailwind's own 65ch
// utility, which wins over the theme's.

import type * as React from "react";
import { PADDING_CLASSES } from "../../lib/steps";
import { cn } from "../../lib/utils";

/** A named page width: the `--container-*` tokens, or no cap. */
export type PageWidth = "form" | "prose" | "panel" | "main" | "dashboard" | "full";

/** The max-width class per page width. `full` is no cap. */
export const PAGE_WIDTH_CLASSES: Record<PageWidth, string> = {
	form: "max-w-form",
	prose: "max-w-(--container-prose)",
	panel: "max-w-panel",
	main: "max-w-main",
	dashboard: "max-w-dashboard",
	full: "max-w-full",
};

/** The responsive side gutter, drawn while no `padding` step is given. */
const GUTTER = "px-4 md:px-8 lg:px-12";

export type ContainerProps = React.ComponentProps<"div"> & {
	/** The cap, a page width name. */
	maxWidth?: PageWidth;
	/** A space step (0..16, 4px each) on every side, in place of the gutter. */
	padding?: number;
};

export function Container({ maxWidth = "main", padding, className, ...props }: ContainerProps) {
	const pad = padding === undefined ? GUTTER : PADDING_CLASSES[padding];
	return (
		<div
			data-slot="container"
			data-max-width={maxWidth}
			className={cn(
				"mx-auto flex w-full min-w-0 flex-col",
				PAGE_WIDTH_CLASSES[maxWidth] ?? PAGE_WIDTH_CLASSES.main,
				pad ?? GUTTER,
				className,
			)}
			{...props}
		/>
	);
}
