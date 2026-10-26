// Container primitive. The page frame: full width up to a named cap, centred.
// Design refs:
//   space-radius.md  §3 container widths (the `--container-*` tokens)
//   space-radius.md  §1 spacing scale (gutter and gap steps)
//
// Fluid below the cap, so the width never jumps at a breakpoint. The one
// thing that follows the window is the side gutter: 16px on a phone, 32px
// from `md`, 48px from `lg`. `padding="none"` drops it for a page that runs
// edge to edge. Children stack down the frame with `gap` between them.
//
// Sizes are the theme's container tokens, spelled out so Tailwind sees every
// class. Prose reads its token by name: `max-w-prose` is Tailwind's own 65ch
// utility, which wins over the theme's.

import type * as React from "react";
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

/** The side gutter: responsive, or none. */
export type ContainerPadding = "gutter" | "none";

const PADDING_CLASSES: Record<ContainerPadding, string> = {
	gutter: "px-4 md:px-8 lg:px-12",
	none: "px-0",
};

export type ContainerProps = React.ComponentProps<"div"> & {
	size?: PageWidth;
	padding?: ContainerPadding;
};

export function Container({
	size = "main",
	padding = "gutter",
	className,
	...props
}: ContainerProps) {
	return (
		<div
			data-slot="container"
			data-size={size}
			className={cn(
				"mx-auto flex w-full min-w-0 flex-col",
				PAGE_WIDTH_CLASSES[size] ?? PAGE_WIDTH_CLASSES.main,
				PADDING_CLASSES[padding] ?? PADDING_CLASSES.gutter,
				className,
			)}
			{...props}
		/>
	);
}
