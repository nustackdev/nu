// PageLinkRef -- a link to a page, drawn as the page: mark, title, a line
// about it and a trailing note. A row in a list of pages, a tile in a grid.
//
// Server-owned, plain props merged by the default store `write`: `href`,
// `title`, `icon`, `description`, `meta`, `variant` ("row", "tile" or
// "inline") and `target` ("_self" or "_blank"). Composes the kit PageLink primitive, which
// is a real <a href>, so a host shell that routes same-origin anchor clicks
// routes these too and the browser's own link handling (open in new tab,
// copy link) is untouched.
//
// `icon` is either a name from the curated lucide set or anything else,
// drawn as text: an emoji, a letter. A name is looked up quietly, so an
// emoji never warns as an unknown icon. With no icon there is no mark.
// A title-less link shows its href, so it stays findable.
//
// "inline" is a mention, Notion style: the mark and the title on one line,
// no description or meta. It keeps its own width in a block flow and runs
// with the text in a Line, wrapping with it.
//
// The props are plain on purpose: a host that knows its pages (a plane of
// cells, a docs tree) fills title and icon from there and writes them here.

import { PageLink } from "../../components/ui/page-link";
import { anchorProps } from "../../lib/anchor";
import { type NodeEntry, type NodeProps, useEnumProp, useStringProp } from "../../tree";
import { ICONS } from "../input/icons";

const VARIANTS = ["row", "tile", "inline"] as const;

function PageLinkView({ path }: NodeProps) {
	const href = useStringProp(path, "href");
	const title = useStringProp(path, "title");
	const icon = useStringProp(path, "icon");
	const description = useStringProp(path, "description");
	const meta = useStringProp(path, "meta");
	const variant = useEnumProp(path, "variant", VARIANTS, "row");
	const target = useStringProp(path, "target", "_self");
	const glyph = Object.hasOwn(ICONS, icon) ? ICONS[icon] : undefined;
	return (
		<PageLink
			{...anchorProps(href, target)}
			variant={variant}
			icon={glyph}
			mark={glyph ? undefined : icon || undefined}
			title={title || href}
			description={description || undefined}
			meta={meta || undefined}
		/>
	);
}

// A row or a tile takes the width it is given; an inline mention is a run of
// text, its own width in a block flow and a word among words in a Line.
export const PageLinkRef: NodeEntry = {
	component: PageLinkView,
	fill: (props) => props.variant !== "inline",
};
