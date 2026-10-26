// Icon primitive. One lucide glyph on the kit's size and tone ladders.
// Design refs:
//   typography.md    §Body sizes (glyph sizes track the text they sit by)
//   palette.md       text tiers, status hues, accent soft fill and washes
//   space-radius.md  §radius md for the framed tile
//
// The glyph is the consumer's: pass any lucide component (or one by name,
// `iconFor` in lib/icons). `tone` "inherit" (the default)
// takes the surrounding text color, so an icon in a sentence or a nav row
// reads as part of it.
//
// `inline` sits the glyph on the text baseline at the text's own size (1em),
// for a run inside a paragraph; the size ladder applies otherwise. `framed`
// sets the glyph in a soft tinted square, the leading mark of a feature list
// or a page header, tinted by the tone (neutral for inherit and the text
// tiers).

import { cva, type VariantProps } from "class-variance-authority";
import type { LucideIcon } from "lucide-react";
import type * as React from "react";

import { TONES, tone as toneClasses } from "../../lib/recipes";
import { cn } from "../../lib/utils";

const iconVariants = cva("shrink-0", {
	variants: {
		size: {
			xs: "size-3", // 12
			sm: "size-3.5", // 14
			md: "size-4", // 16
			lg: "size-5", // 20
			xl: "size-6", // 24
		},
		// The kit's tone ladder (lib/recipes.ts), plus `inherit`: no ink of
		// its own, the surrounding text's color.
		tone: { inherit: "", ...toneClasses },
	},
	defaultVariants: {
		size: "md",
		tone: "inherit",
	},
});

/** Icon sizes and tones by key, for a node checking a prop off the wire. */
export const ICON_SIZES = ["xs", "sm", "md", "lg", "xl"] as const;
export const ICON_TONES = ["inherit", ...TONES] as const;

// The framed square: the glyph plus 8px a side at md, so a framed md icon
// is a 32px tile, one control row high.
const frameVariants = cva("inline-flex shrink-0 items-center justify-center rounded-md", {
	variants: {
		size: {
			xs: "p-1",
			sm: "p-1.5",
			md: "p-2",
			lg: "p-2.5",
			xl: "p-3",
		},
		tone: {
			inherit: "bg-bg-sunken",
			primary: "bg-bg-sunken",
			secondary: "bg-bg-sunken",
			muted: "bg-bg-sunken",
			accent: "bg-accent-soft",
			ok: "bg-status-ok-wash",
			warn: "bg-status-warn-wash",
			danger: "bg-status-danger-wash",
			info: "bg-status-info-wash",
		},
	},
	defaultVariants: {
		size: "md",
		tone: "inherit",
	},
});

export type IconSize = NonNullable<VariantProps<typeof iconVariants>["size"]>;
export type IconTone = NonNullable<VariantProps<typeof iconVariants>["tone"]>;

export interface IconProps
	extends Omit<React.SVGAttributes<SVGSVGElement>, "children">,
		VariantProps<typeof iconVariants> {
	icon: LucideIcon;
	/** Text size, on the baseline: a run in a sentence. Ignores `size`. */
	inline?: boolean;
	/** Set in a soft tinted square. */
	framed?: boolean;
	/** What a screen reader calls it. Unset, the glyph is decorative. */
	label?: string;
}

export function Icon({
	icon: Glyph,
	size,
	tone,
	inline = false,
	framed = false,
	label,
	className,
	...props
}: IconProps) {
	const a11y = label ? { role: "img", "aria-label": label } : { "aria-hidden": true };
	const glyph = (
		<Glyph
			data-slot="icon"
			className={cn(
				iconVariants({ size, tone }),
				inline && "inline size-[1em] align-[-0.125em]",
				framed && tone === "inherit" && "text-text-secondary",
				!framed && className,
			)}
			{...a11y}
			{...props}
		/>
	);
	if (!framed) return glyph;
	return (
		<span data-slot="icon-frame" className={cn(frameVariants({ size, tone }), className)}>
			{glyph}
		</span>
	);
}

export { frameVariants, iconVariants };
