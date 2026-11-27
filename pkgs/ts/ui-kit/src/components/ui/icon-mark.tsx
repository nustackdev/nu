// IconMark: one stored icon, drawn. A lucide glyph or an emoji, in the same box.
// Design refs:
//   typography.md    §Body sizes (the emoji is text, sized to fill the box)
//   palette.md       text tiers (a glyph takes the text color, an emoji keeps its own)
//
// `icon` is a stored value ("lucide:folder", "emoji:🌱", a bare lucide name)
// or one already read (`parseIcon`, ./icon-picker-model.ts). A value that
// reads as no icon draws `fallback`, and nothing when there is none, so a bad
// value never breaks a row.
//
// The two kinds sit in the same box at every size: 16 by a line of text (sm),
// 20 in the picker's cells (md), 32 before a page title (lg). The emoji is
// centred in the box with its line box collapsed, and drawn in the platform's
// colour font (`font-emoji`, theme.css).
//
// Decorative unless `label` is set: the text beside it usually names the
// thing. The ref reaches the element, so a popover can anchor on it.

import type * as React from "react";

import { iconFor } from "../../lib/icons";
import { cn } from "../../lib/utils";
import { type IconValue, parseIcon } from "./icon-picker-model";

export type IconMarkSize = "sm" | "md" | "lg";

const BOX: Record<IconMarkSize, string> = { sm: "size-4", md: "size-5", lg: "size-8" };

const EMOJI_TEXT: Record<IconMarkSize, string> = {
	sm: "text-lg",
	md: "text-2xl",
	lg: "text-display",
};

export interface IconMarkProps {
	/** A stored value, or an icon already read. */
	icon: string | IconValue | null | undefined;
	/** What draws when `icon` reads as none. */
	fallback?: string | IconValue;
	size?: IconMarkSize;
	/** What a screen reader calls it. Unset, the mark is decorative. */
	label?: string;
	className?: string;
	ref?: React.Ref<HTMLElement & SVGSVGElement>;
}

function read(icon: string | IconValue | null | undefined): IconValue | null {
	return typeof icon === "string" || icon == null ? parseIcon(icon) : icon;
}

function IconMark({ icon, fallback, size = "sm", label, className, ref }: IconMarkProps) {
	const shown = read(icon) ?? read(fallback);
	if (!shown) return null;
	const a11y = label ? { role: "img", "aria-label": label } : { "aria-hidden": true };
	if (shown.kind === "emoji") {
		return (
			<span
				ref={ref}
				data-slot="icon-mark"
				data-kind="emoji"
				{...a11y}
				className={cn(
					"inline-flex shrink-0 select-none items-center justify-center overflow-visible",
					"font-emoji",
					BOX[size],
					EMOJI_TEXT[size],
					// After the size: the merge drops a leading that comes before a text size.
					"leading-none",
					className,
				)}
			>
				{shown.char}
			</span>
		);
	}
	const Glyph = iconFor(shown.name);
	if (!Glyph) return null;
	return (
		<Glyph
			ref={ref}
			data-slot="icon-mark"
			data-kind="lucide"
			{...a11y}
			className={cn("shrink-0", BOX[size], className)}
		/>
	);
}

export { IconMark };
