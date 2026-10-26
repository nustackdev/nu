// LinkRef -- a text link: an anchor with href, label, target, and an optional
// external indicator.
//
// Server-owned. A write is a partial merge of {href, label, target, external,
// variant, icon, arrow} into the node's props, which is the default store
// behaviour, so there is no handler. The `external` slot is tri-state: true
// forces the indicator, false suppresses it, nil means "auto" (true when
// target is _blank or the href host differs), and that read is done at
// render time.
//
// `variant` picks the ink. `text` (the default) is a plain text link in
// Starlight (content, not navigation), with the hand cursor of a link in
// prose; `muted` is the same link in the secondary ink, for a footer or a
// byline. A link that looks like a button is a ButtonRef with an href, not
// a look of this one; an old `button` / `primary` / ... variant draws as
// `text`. `icon` is a lucide name (../../lib/icons) drawn before the
// label; `arrow` draws a trailing arrow, for a "read more". The external
// glyph and the arrow never both draw: arrow wins.
//
// It is a real <a href> through `anchorProps`, so a host's AnchorCatcher
// routes a same-origin one and the browser keeps the rest.
//
// In a Line (inline flow) a text link is an inline anchor, not an
// inline-flex box, so a long label wraps with the sentence; the glyph rides
// the last word.

import { ArrowRight, ExternalLink } from "lucide-react";
import { anchorProps, crossHost, normTarget } from "../../lib/anchor";
import { iconFor } from "../../lib/icons";
import { cn } from "../../lib/utils";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useFlow,
	useProp,
	useStringProp,
} from "../../tree";

function normalizeExternal(v: unknown): boolean | null {
	if (v === true) return true;
	if (v === false) return false;
	return null;
}

const TEXT_TONES: Record<string, string> = {
	text: "text-accent-2 hover:text-accent-2-hover",
	muted: "text-text-secondary hover:text-text-primary",
};

function LinkView({ path }: NodeProps) {
	const href = useStringProp(path, "href");
	const label = useStringProp(path, "label");
	const target = normTarget(useStringProp(path, "target", "_self"));
	const external = normalizeExternal(useProp<unknown>(path, "external", null));
	const variant = useStringProp(path, "variant", "text");
	const iconName = useStringProp(path, "icon");
	const arrow = useBoolProp(path, "arrow");
	const showExternal =
		!arrow && (external === true || (external == null && (target === "_blank" || crossHost(href))));
	const text = label !== "" ? label : href;
	const anchor = anchorProps(href, target);
	const inline = useFlow() === "inline";
	const Icon = iconFor(iconName);
	const glyph = cn("size-3.5 shrink-0", inline && "inline align-[-0.125em]");
	return (
		<a
			data-slot="link"
			data-variant={variant === "muted" ? "muted" : "text"}
			{...anchor}
			className={cn(
				inline ? "inline" : "inline-flex items-center gap-1",
				"cursor-pointer rounded-sm",
				TEXT_TONES[variant] ?? TEXT_TONES.text,
				"underline-offset-2 hover:underline",
				"transition-colors duration-fast ease-out",
				"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
			)}
		>
			{Icon ? <Icon aria-hidden="true" className={cn(glyph, inline && "me-1")} /> : null}
			<span>{text}</span>
			{arrow ? <ArrowRight aria-hidden="true" className={cn(glyph, inline && "ms-1")} /> : null}
			{showExternal ? (
				<ExternalLink aria-hidden="true" className={cn(glyph, inline && "ms-1")} />
			) : null}
		</a>
	);
}

export const LinkRef: NodeEntry = { component: LinkView };
