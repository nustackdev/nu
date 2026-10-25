// PageLink primitive. A link to a page, drawn as the page: its mark, its
// title, a line about it, and a trailing note. A row in a list of pages, a
// tile in a grid of them, or `inline`: a mention, just the mark and the
// title on one line, at home in a paragraph or on a line of its own.
// Design refs:
//   typography.md    §Body (title base/lg medium, description sm secondary,
//                    meta xs muted)
//   palette.md       bg-hover / bg-press rows, border tiers on the tile
//   elevation.md     level 0 tile (border-default, strong on hover)
//   cursor.md        in-app navigation keeps the arrow
//   space-radius.md  §radius md rows, lg tiles; §Density 32px mark at md
//   motion.md        §3 row hover (bg + color, duration-fast ease-out)
//
// Always a real <a href>: a host shell routes same-origin clicks on anchors,
// and middle click, copy link and open in new tab work for free. The mark is
// a lucide glyph (`icon`) or a text node (`mark`: an emoji, a letter); in a
// row or a tile it sits in the Icon frame, a fixed square, so a list of
// pages lines up whatever each mark is. Description clamps to one line in a
// row and two in a tile; title truncates. Inline drops the frame, the
// description and the meta, and underlines the title quietly (a hairline,
// not the accent of a text link): it is a page, not a sentence's link.

import { cva, type VariantProps } from "class-variance-authority";
import type { LucideIcon } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";
import { frameVariants, Icon } from "./icon";

const pageLinkVariants = cva(
	[
		"group/page-link min-w-0 text-text-primary no-underline",
		"cursor-default focus-ring",
		"transition-colors duration-fast ease-out",
	].join(" "),
	{
		variants: {
			variant: {
				row: "flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-bg-hover active:bg-bg-press",
				// Level 0, the same as an interactive Card: the default line at
				// rest, the strong one under the pointer, no wash.
				tile: [
					"flex flex-col gap-3 rounded-lg border border-border-default bg-bg-surface p-4",
					"hover:border-border-strong",
				].join(" "),
				// A mention: mark and title in the run of the text, a hover wash
				// and nothing else. `box-decoration-clone` keeps the wash's
				// rounded ends when a Line wraps it.
				inline:
					"inline rounded-md px-0.5 box-decoration-clone hover:bg-bg-hover active:bg-bg-press",
			},
		},
		defaultVariants: {
			variant: "row",
		},
	},
);

type PageLinkVariant = NonNullable<VariantProps<typeof pageLinkVariants>["variant"]>;

// The mark's square: 32px in a row (one control row high), 40px on a tile,
// the Icon primitive's framed md and lg. A glyph is drawn framed by Icon
// itself, so its frame is the square; a text mark (an emoji, a letter) gets
// the same frame from `frameVariants`, sized to the square.
const MARK_SIZE = { row: "md", tile: "lg" } as const;
const TEXT_MARK = { row: "size-8 text-xl", tile: "size-10 text-2xl" } as const;

export interface PageLinkProps
	extends Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, "title">,
		VariantProps<typeof pageLinkVariants> {
	title: React.ReactNode;
	/** The page's glyph, drawn as its mark. Wins over `mark`. */
	icon?: LucideIcon;
	/** A text mark: an emoji or a letter. None (and no icon) leaves no square. */
	mark?: React.ReactNode;
	/** A line about the page. Not drawn inline. */
	description?: React.ReactNode;
	/** A trailing note: a date, a count, an owner. Not drawn inline. */
	meta?: React.ReactNode;
}

function Mark({
	variant,
	icon,
	mark,
}: {
	variant: PageLinkVariant;
	icon?: LucideIcon;
	mark?: React.ReactNode;
}) {
	if (variant === "inline") {
		// No frame: the glyph or the emoji at the text's own size.
		return (
			<span data-slot="page-link-mark" aria-hidden="true" className="me-1">
				{icon ? <Icon icon={icon} inline className="text-text-secondary" /> : mark}
			</span>
		);
	}
	if (icon) {
		return (
			<span data-slot="page-link-mark" className="inline-flex shrink-0">
				<Icon icon={icon} framed size={MARK_SIZE[variant]} />
			</span>
		);
	}
	return (
		<span
			data-slot="page-link-mark"
			aria-hidden="true"
			className={cn(
				frameVariants({ size: MARK_SIZE[variant] }),
				"p-0 leading-none text-text-secondary",
				TEXT_MARK[variant],
			)}
		>
			{mark}
		</span>
	);
}

export function PageLink({
	variant: variantProp,
	title,
	icon,
	mark,
	description,
	meta,
	className,
	...props
}: PageLinkProps) {
	const variant: PageLinkVariant = variantProp ?? "row";
	const markEl = icon || mark ? <Mark variant={variant} icon={icon} mark={mark} /> : null;
	if (variant === "inline") {
		return (
			<a
				data-slot="page-link"
				data-variant="inline"
				className={cn(pageLinkVariants({ variant }), className)}
				{...props}
			>
				{markEl}
				<span
					data-slot="page-link-title"
					className="font-medium underline decoration-border-subtle underline-offset-2"
				>
					{title}
				</span>
			</a>
		);
	}
	const tile = variant === "tile";
	const text = (
		<span className="flex min-w-0 flex-1 flex-col gap-0.5">
			<span
				data-slot="page-link-title"
				className={cn("truncate font-medium", tile ? "text-lg" : "text-base")}
			>
				{title}
			</span>
			{description ? (
				<span
					data-slot="page-link-description"
					className={cn("text-sm text-text-secondary", tile ? "line-clamp-2" : "truncate")}
				>
					{description}
				</span>
			) : null}
		</span>
	);
	const metaEl = meta ? (
		<span
			data-slot="page-link-meta"
			className={cn("shrink-0 text-xs text-text-muted", tile && "mt-auto")}
		>
			{meta}
		</span>
	) : null;
	return (
		<a
			data-slot="page-link"
			data-variant={variant}
			className={cn(pageLinkVariants({ variant }), className)}
			{...props}
		>
			{markEl}
			{text}
			{metaEl}
		</a>
	);
}

export { pageLinkVariants };
